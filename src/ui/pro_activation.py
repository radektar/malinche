import webbrowser
import rumps
from src.config.license import license_manager
from src.config.features import FeatureTier


def show_pro_activation():
    """Show PRO activation dialog."""
    features = license_manager.get_features()
    tier = license_manager.get_current_tier()

    if tier != FeatureTier.FREE:
        tier_name = "PRO Individual" if tier == FeatureTier.PRO else "PRO Organization"
        rumps.alert(
            title="✅ Malinche PRO",
            message=f"Masz już aktywną subskrypcję {tier_name}!"
        )
        return

    # Show upgrade prompt
    response = rumps.alert(
        title="🚀 Malinche PRO",
        message=(
            "Odblokuj pełne możliwości Malinche:\n\n"
            "⭐ AI Podsumowania i tytuły\n"
            "⭐ Inteligentne tagi Obsidian\n"
            "⭐ Diaryzacja (kto mówi kiedy)\n"
            "⭐ Współdzielona wiedza (PRO Org)\n\n"
            "Subskrypcja PRO Individual już od $9/mies."
        ),
        ok="Kup PRO",
        cancel="Mam już klucz"
    )

    if response == 1:
        # Open purchase page
        webbrowser.open("https://transrec.app/pro")
    elif response == 0:
        # Show key input
        key_response = rumps.Window(
            title="Aktywacja PRO",
            message="Wklej klucz licencyjny:",
            ok="Aktywuj",
            cancel="Anuluj",
            dimensions=(300, 24)
        ).run()

        if key_response.clicked == 1 and key_response.text:
            success, message = license_manager.activate_license(key_response.text.strip())
            rumps.alert(
                title="✅ Sukces" if success else "❌ Błąd",
                message=message
            )


def show_pro_status():
    """Check and show current license status."""
    tier = license_manager.get_current_tier()
    if tier == FeatureTier.FREE:
        show_pro_activation()
    else:
        limits = license_manager.get_usage_limits()
        tier_name = "PRO Individual" if tier == FeatureTier.PRO else "PRO Organization"
        
        message = f"Aktywna subskrypcja: {tier_name}\n"
        if not limits.get("unlimited"):
            message += f"Pozostało minut: {limits.get('minutes_monthly', 0)} / miesiąc"
        else:
            message += "Nielimitowane przetwarzanie"
            
        rumps.alert(
            title="💎 Status Malinche PRO",
            message=message
        )
