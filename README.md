![alt text](https://github.com/MLUX-University-of-Vienna/ProcessMiningVisualization_SS24_Frauenberger/blob/master/VisuPM.jpg?raw=true)

# Process Mining Visualization

A desktop application for importing event logs, mining and visualizing process models using various algorithms (Heuristic Miner, Inductive Miner, Fuzzy Miner) with configurable metrics for filtering nodes and edges. Process models can be exported as images.

## Status

**Version:** 0.2.0  
**Status:** Production Ready

### Implemented Algorithms
- ✅ Heuristic Miner
- ✅ Fuzzy Miner  
- ✅ Inductive Miner (including IMf and IMd variants)

## Project Structure

```
Process_Mining_Visualisation/
├── src/                          # Source code
│   ├── app.py                    # Main Streamlit application entry
│   ├── config.py                 # Configuration and constants
│   ├── core/                     # Core business logic
│   │   ├── algorithms/           # Mining algorithm implementations
│   │   ├── graphs/               # Graph structures (DFG, cuts)
│   │   ├── log_processing/       # Log filters and splits
│   │   └── analysis/             # Detection and prediction models
│   ├── io/                       # Import/Export operations
│   ├── ui/                       # User interface
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/                # Page controllers and views
│   │   │   ├── algorithms/       # Algorithm-specific UIs
│   │   │   ├── data/             # Data handling pages
│   │   │   └── tools/            # Utility pages
│   │   └── theme.py              # Theme management
│   ├── transformations/          # Data transformations
│   ├── exceptions/               # Custom exceptions
│   └── utils/                    # Shared utilities
├── tests/                        # Test suite
│   ├── fixtures/                 # Test data (CSV, logs)
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── docs/                         # Documentation
│   ├── algorithms/               # Algorithm specifications
│   ├── diagrams/                 # Architecture diagrams
│   ├── guides/                   # User guides
│   └── research/                 # Academic papers
├── data/                         # Sample data
│   └── samples/                  # Example event logs
├── .streamlit/                   # Streamlit configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Quick Start

### Prerequisites

- **Python** 3.10+ (tested with 3.10.7, 3.11.6, 3.12.2)
- **Graphviz** - [Download here](https://graphviz.org/)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Process_Mining_Visualisation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   
   Windows (PowerShell):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   
   Windows (CMD):
   ```cmd
   .venv\Scripts\activate.bat
   ```
   
   Linux/macOS:
   ```bash
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify Graphviz installation**
   ```bash
   dot -V
   ```
   
   If not found, add Graphviz to your PATH:
   - **Windows:** Add `C:\Program Files\Graphviz\bin` to PATH
   - **Linux/macOS:** Add `export PATH="/path/to/graphviz/bin:$PATH"` to `.bashrc`

### Running the Application

```bash
cd src
streamlit run app.py
```

The application will open in your default browser.

## Testing

### Install test dependencies
```bash
pip install -r tests/test_requirements.txt
```

### Run all tests
```bash
python -m pytest tests/
```

### Run specific test module
```bash
python -m pytest tests/unit/core/algorithms/
```

### Run with coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```
