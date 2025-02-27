from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

# Collect all streamlit sub-modules
hiddenimports = collect_submodules('streamlit')

# Collect streamlit data files (e.g., metadata, static assets)
# datas = collect_data_files('streamlit')

datas = copy_metadata('streamlit')