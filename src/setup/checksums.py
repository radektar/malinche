"""Checksums, URLs, and versions for dependencies."""

# Wersje zależności
VERSIONS = {
    "whisper": "1.1.0",
    "whisper_distribution": "static",
    "ffmpeg": "6.1",
    "model_small": "latest",
}

# SHA256 checksums (verified from deps-v1.0.0 release)
CHECKSUMS = {
    # Verified from deps-v1.1.0 release assets.
    "whisper-bundled-arm64.tar.gz": "0da3355a879260d23c2e31e082e36de1d19d9d25fb8045771b3bc679f6c1dc22",
    "whisper-cli": "ddb643d77e6d479ee9e1b7beafa2a9f174c58ab048db2f412bf85fc1ff3e5362",
    "ffmpeg-arm64": "b68f795f7fb4528daf697f57a2b6780846a1ae762a71907e994442ad103ee88f",
    "ggml-small.bin": "1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b",
}

# URLs dla pobierania
URLS = {
    "whisper": "https://github.com/radektar/transrec/releases/download/deps-v1.1.0/whisper-cli",
    "ffmpeg": "https://github.com/radektar/transrec/releases/download/deps-v1.1.0/ffmpeg-arm64",
    "model_small": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
}

# Oczekiwane rozmiary plików (w bajtach) - verified from release
SIZES = {
    # Verified from deps-v1.1.0 release assets.
    "whisper-bundled-arm64.tar.gz": 1_294_021,  # ~1.2MB
    "whisper-cli": 3_138_072,  # ~3.0MB
    "ffmpeg-arm64": 80_269_896,  # ~76MB
    "ggml-small.bin": 487_601_967,  # ~465MB
}

