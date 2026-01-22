# Fonts

This project can generate Chinese PDFs. For consistent cross-platform rendering (and to avoid noisy fontTools subsetting logs when using macOS system TTC fonts), we recommend installing an open-licensed Noto font locally in this repo.

## Recommended font
- **Noto Sans SC** (Simplified Chinese)
- License: SIL Open Font License (OFL)

## Install
Run:

- `./scripts/download_fonts.sh`

This will download:
- `fonts/NotoSansSC-Regular.otf`
- `fonts/NotoSansSC-Bold.otf`

If these files are present, the PDF generator will prefer them automatically.

## Notes
- Font files are not committed to the repo (large binaries).
- In restricted environments without outbound network access, the download script may be unable to fetch fonts. In that case, the PDF generator falls back to system fonts.
