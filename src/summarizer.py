"""AI-powered summarization for transcripts."""

import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from src.config import config
from src.logger import logger

Anthropic = None  # type: ignore[assignment]


class APIBillingError(Exception):
    """Claude API credit_balance exhausted (HTTP 400 invalid_request_error)."""


def _is_permanent_api_error(exc: BaseException) -> str | None:
    """Return error reason string when *exc* is a permanent Anthropic API error, else None."""
    status = getattr(exc, "status_code", None)
    message = str(getattr(exc, "message", exc)).lower()
    exc_str = str(exc).lower()
    if status == 400 and ("credit balance" in message or "credit balance is too low" in exc_str):
        return "billing"
    if status == 404 and ("model" in message or "not_found" in exc_str):
        return "model_not_found"
    return None


def _is_credit_balance_error(exc: BaseException) -> bool:
    """Return True when *exc* is an Anthropic 400 credit_balance error."""
    return _is_permanent_api_error(exc) == "billing"


class BaseSummarizer(ABC):
    """Base class for transcript summarizers.
    
    Provides interface for generating summaries and titles from transcripts.
    All summarizer implementations should inherit from this class.
    """
    
    @abstractmethod
    def generate(self, transcript: str) -> Dict[str, str]:
        """Generate summary and title from transcript.
        
        Args:
            transcript: Full transcription text
            
        Returns:
            Dict with 'title' and 'summary' keys
            
        Raises:
            Exception: If summarization fails
        """
        pass


class ClaudeSummarizer(BaseSummarizer):
    """Claude API-based summarizer.
    
    Uses Anthropic's Claude API to generate summaries and titles
    from transcriptions in Polish.
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """Initialize Claude summarizer.
        
        Args:
            api_key: Anthropic API key
            model: Claude model name
        """
        global Anthropic
        try:
            from anthropic import Anthropic as AnthropicClient
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
        if Anthropic is None:
            Anthropic = AnthropicClient
        
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_words = config.SUMMARY_MAX_WORDS
        self.title_max_length = config.TITLE_MAX_LENGTH
    
    def generate(self, transcript: str) -> Dict[str, str]:
        """Generate summary and title from transcript using Claude API.
        
        Args:
            transcript: Full transcription text
            
        Returns:
            Dict with 'title' and 'summary' keys
            
        Raises:
            Exception: If API call fails
        """
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript provided, using fallback")
            return self._fallback_summary()
        
        # Truncate transcript if too long (Claude has token limits)
        # Keep last 10000 characters to preserve context
        max_transcript_length = 10000
        if len(transcript) > max_transcript_length:
            logger.debug(
                f"Transcript too long ({len(transcript)} chars), "
                f"truncating to last {max_transcript_length} chars"
            )
            transcript = transcript[-max_transcript_length:]
        
        prompt = self._build_prompt(transcript)
        
        try:
            logger.debug(f"Calling Claude API (model: {self.model})")
            start_time = time.time()
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                timeout=30.0,  # 30 second timeout
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            elapsed = time.time() - start_time
            logger.debug(f"Claude API call completed in {elapsed:.2f}s")
            
            # Extract response
            response_text = message.content[0].text if message.content else ""
            
            # Parse response (expects format: TITLE: ...\n\nSUMMARY: ...)
            title, summary = self._parse_response(response_text)
            
            # Ensure title is within limits
            if len(title) > self.title_max_length:
                title = title[:self.title_max_length - 3] + "..."
            
            return {
                "title": title.strip(),
                "summary": summary.strip()
            }
            
        except Exception as e:
            reason = _is_permanent_api_error(e)
            if reason:
                logger.critical(
                    "❌ Claude API permanent error (summarizer, reason=%s): %s",
                    reason,
                    e,
                )
                raise APIBillingError(str(e)) from e
            logger.error(f"Claude API error: {e}", exc_info=True)
            logger.warning("Falling back to simple title generation")
            return self._fallback_summary(transcript)
    
    def _build_prompt(self, transcript: str) -> str:
        """Build prompt for Claude API.
        
        Args:
            transcript: Transcription text
            
        Returns:
            Formatted prompt string
        """
        return f"""Przeanalizuj poniższą transkrypcję nagrania audio i wygeneruj:

1. KRÓTKI TYTUŁ (maksymalnie {self.title_max_length} znaków) - powinien być zwięzły i opisowy

2. PODSUMOWANIE w formacie markdown zawierające następujące sekcje:

   ## Podsumowanie
   - 5-7 zdań opisujących kluczowe spostrzeżenia ze spotkania
   - Używaj **pogrubienia** dla najważniejszych pojęć, decyzji i zobowiązań
   - Używaj *kursywy* dla dodatkowego kontekstu lub uwag
   - Możesz używać blockquotes (`>`) dla ważnych stwierdzeń
   - Wykorzystuj pełne możliwości markdown: listy numerowane, tabele (gdy odpowiednie), separatory (`---`)

   ## Kluczowe punkty
   - Sekcja z punktami podzielonymi według priorytetu używając emoji:
     - ⚠️ **Krytyczne:** Najważniejsze decyzje, zobowiązania, terminy wymagające natychmiastowej uwagi
     - ⚡ **Ważne:** Istotne tematy, które wymagają monitorowania lub dalszych działań
     - 📝 **Informacyjne:** Dodatkowe informacje, kontekst, tło rozmowy
   - Każdy punkt powinien być konkretny i zwięzły
   - Używaj **pogrubienia** dla kluczowych słów w każdym punkcie
   - Skup się na elementach, na których należy się skupić po spotkaniu

   ## Cytaty
   - Sekcja z bezpośrednimi cytatami z transkrypcji, pogrupowanymi tematycznie
   - Każdy temat powinien mieć nagłówek poziomu 3 (###)
   - Cytaty formatuj jako blockquotes (`>`) z dodatkowym kontekstem
   - Format dla każdego cytatu:
     > "Dokładny cytat z transkrypcji"
     > — *Kontekst: [krótki opis sytuacji, w której został wypowiedziany]*
   - Wybierz 3-5 najważniejszych cytatów, które najlepiej ilustrują kluczowe wątki rozmowy
   - Cytaty MUSZĄ być rzeczywistymi fragmentami z transkrypcji (nie parafrazami)
   - Cytaty powinny potwierdzać i uzupełniać informacje z sekcji "Podsumowanie"
   - Grupuj cytaty tematycznie - każdy temat w osobnej sekcji z nagłówkiem ###

   ## Lista działań (To-do)
   - 3-5 konkretnych zadań do wykonania po spotkaniu
   - Każde zadanie w formie listy punktowanej (zaczynającej się od "-")
   - Zadania powinny zaczynać się od czasownika w trybie rozkazującym (np. "Przygotować...", "Skontaktować się...")
   - Możesz używać checkboxów (`- [ ]`) dla zadań wymagających wykonania

STYLOWANIE MARKDOWN:
- Wykorzystuj pełne możliwości markdown: **pogrubienie**, *kursywa*, `kod inline`, blockquotes (`>`), listy numerowane, tabele (gdy odpowiednie)
- Używaj separatorów (`---`) między większymi sekcjami jeśli potrzebne
- Formatuj cytaty jako blockquotes dla lepszej czytelności
- Używaj emoji (⚠️ ⚡ 📝) konsekwentnie dla priorytetów w sekcji Kluczowe punkty

WAŻNE:
- Podsumowanie powinno być zwięzłe i skupiać się na najważniejszych wnioskach
- Cytaty MUSZĄ być rzeczywistymi fragmentami z transkrypcji (nie parafrazami)
- Cytaty grupuj tematycznie - każdy temat w osobnej sekcji z nagłówkiem ###
- Lista zadań powinna zawierać tylko konkretne, wykonalne akcje
- Używaj wyłącznie języka polskiego
- Formatuj odpowiedź jako markdown z pełnym wykorzystaniem możliwości stylowania

Odpowiedz WYŁĄCZNIE w formacie:
TITLE: [tytuł]
SUMMARY: [podsumowanie w formacie markdown z sekcjami: ## Podsumowanie, ## Kluczowe punkty, ## Cytaty, ## Lista działań (To-do)]

Transkrypcja:
{transcript}"""
    
    def _parse_response(self, response_text: str) -> Tuple[str, str]:
        """Parse Claude API response.
        
        Args:
            response_text: Raw response from API
            
        Returns:
            Tuple of (title, summary) where summary contains markdown formatting
        """
        title = ""
        summary_lines = []
        
        lines = response_text.split("\n")
        current_section = None
        
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("TITLE:"):
                title = stripped_line.replace("TITLE:", "").strip()
                current_section = "title"
            elif stripped_line.startswith("SUMMARY:"):
                # Start collecting summary, preserve the line after SUMMARY:
                summary_content = stripped_line.replace("SUMMARY:", "").strip()
                if summary_content:
                    summary_lines.append(summary_content)
                current_section = "summary"
            elif current_section == "summary":
                # Preserve markdown formatting - keep empty lines and indentation
                if stripped_line or summary_lines:  # Include empty lines for markdown spacing
                    summary_lines.append(line)
        
        summary = "\n".join(summary_lines).strip()
        
        # Fallback if parsing failed
        if not title or not summary:
            # Try to extract first line as title, rest as summary
            parts = response_text.split("\n\n", 1)
            if len(parts) >= 2:
                title = parts[0].strip()[:self.title_max_length]
                summary = parts[1].strip()
                # Ensure summary has markdown structure if missing
                if not summary.startswith("##"):
                    summary = f"## Podsumowanie\n\n{summary[:self.max_words * 6]}"
            elif parts:
                title = parts[0].strip()[:self.title_max_length]
                summary = f"## Podsumowanie\n\n{parts[0].strip()[:self.max_words * 6]}"
        
        # Ensure summary has basic markdown structure if completely missing
        if not summary or summary == "Brak podsumowania":
            summary = """## Podsumowanie

Brak podsumowania.

## Kluczowe punkty

⚠️ **Krytyczne:**
- Przejrzeć transkrypcję ręcznie

⚡ **Ważne:**
- Wyciągnąć kluczowe wnioski ze spotkania

📝 **Informacyjne:**
- Sprawdzić pełną transkrypcję poniżej

## Cytaty

*Brak cytatów - wymagana ręczna analiza transkrypcji*

## Lista działań (To-do)

- Przejrzeć transkrypcję ręcznie"""
        
        return title or "Nagranie", summary
    
    def _fallback_summary(self, transcript: Optional[str] = None) -> Dict[str, str]:
        """Generate fallback summary when API fails.
        
        Args:
            transcript: Optional transcript text for basic extraction
            
        Returns:
            Dict with basic title and summary in markdown format
        """
        if transcript:
            # Extract first sentence or first 50 chars as title
            first_line = transcript.split("\n")[0].strip()
            title = first_line[:self.title_max_length] if first_line else "Nagranie"
            # Use first 200 chars as summary with markdown structure
            summary_text = transcript[:200].strip() + "..."
            summary = f"""## Podsumowanie

{summary_text}

## Kluczowe punkty

⚠️ **Krytyczne:**
- Przejrzeć transkrypcję i wyciągnąć kluczowe wnioski

⚡ **Ważne:**
- Zidentyfikować następne kroki do wykonania

📝 **Informacyjne:**
- Przeanalizować pełną transkrypcję poniżej

## Cytaty

*Brak cytatów - wymagana ręczna analiza transkrypcji*

## Lista działań (To-do)

- Przejrzeć transkrypcję i wyciągnąć kluczowe wnioski
- Zidentyfikować następne kroki do wykonania"""
        else:
            title = "Nagranie"
            summary = """## Podsumowanie

Nie udało się wygenerować podsumowania.

## Kluczowe punkty

⚠️ **Krytyczne:**
- Przejrzeć transkrypcję ręcznie

⚡ **Ważne:**
- Wyciągnąć kluczowe wnioski ze spotkania

📝 **Informacyjne:**
- Sprawdzić pełną transkrypcję poniżej

## Cytaty

*Brak cytatów - wymagana ręczna analiza transkrypcji*

## Lista działań (To-do)

- Przejrzeć transkrypcję ręcznie
- Wyciągnąć kluczowe wnioski ze spotkania"""
        
        return {
            "title": title,
            "summary": summary
        }


from src.config.license import license_manager

def get_summarizer() -> Optional[BaseSummarizer]:
    """Factory function to create appropriate summarizer instance.
    
    Returns:
        Summarizer instance or None if summarization is disabled/unavailable
    """
    # PRO or BYOK (own Anthropic key): summaries require one or the other
    features = license_manager.get_features()
    byok_claude = (
        config.LLM_PROVIDER == "claude" and bool(config.LLM_API_KEY)
    )
    if not features.ai_summaries:
        if byok_claude:
            logger.info(
                "BYOK: AI summaries enabled via customer ANTHROPIC_API_KEY "
                "(no PRO license required)"
            )
        else:
            logger.info(
                "AI summaries require PRO license or BYOK Claude key — skipping"
            )
            return None

    if not config.ENABLE_SUMMARIZATION:
        logger.debug("Summarization disabled in config")
        return None
    
    if config.LLM_PROVIDER == "claude":
        if not config.LLM_API_KEY:
            logger.warning("Claude API key not found, summarization disabled")
            return None
        
        try:
            return ClaudeSummarizer(
                api_key=config.LLM_API_KEY,
                model=config.LLM_MODEL
            )
        except ImportError:
            logger.error(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Claude summarizer: {e}")
            return None
    
    elif config.LLM_PROVIDER == "ollama":
        # Placeholder for future Ollama implementation
        logger.warning("Ollama summarizer not yet implemented")
        return None
    
    else:
        logger.warning(f"Unknown LLM provider: {config.LLM_PROVIDER}")
        return None

