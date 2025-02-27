# Step 1: Install Python
python --version

# Step 2: Install virtualenv
pip install virtualenv

# Step 3: Create virtual environment
python -m venv venv

# Step 4: Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Step 5: Install dependencies
pip install -r requirements.txt

# Step 6: Run the application
streamlit run main.py

# Step 7: Deactivate virtual environment
deactivate

