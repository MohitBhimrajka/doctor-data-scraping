# Doctor Discovery Frontend

A Streamlit-based frontend application for discovering and comparing doctors across India.

## Features

- Search for doctors by specialization and city
- Country-wide search with city tier filtering
- Advanced filtering and sorting options
- Interactive data visualization
- Doctor profile comparison
- Export results in multiple formats
- Keyboard shortcuts for improved UX
- Favorites functionality
- Responsive design

## Project Structure

```
frontend/app/
├── components/           # UI components
│   ├── search_form.py   # Search form component
│   ├── filters.py       # Filters component
│   ├── results_table.py # Results table component
│   └── doctor_profile.py # Doctor profile component
├── services/            # Service layer
│   └── api_client.py    # API client
├── utils/              # Utility functions
│   ├── formatting.py   # Data formatting
│   └── validation.py   # Input validation
├── tests/              # Test files
│   ├── conftest.py     # Test configuration
│   ├── test_search_form.py
│   ├── test_filters.py
│   ├── test_results_table.py
│   ├── test_api_client.py
│   └── test_utils.py
├── main.py             # Main application
├── requirements.txt    # Dependencies
└── pytest.ini         # Test configuration
```

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run main.py
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.

# Run specific test file
pytest tests/test_search_form.py

# Run tests with verbose output
pytest -v
```

### Test Coverage

The project uses pytest-cov for test coverage reporting. Coverage reports are generated in:
- Terminal output (--cov-report=term-missing)
- HTML format (--cov-report=html)

### Test Categories

- Unit Tests: Test individual components and functions
- Integration Tests: Test component interactions
- Async Tests: Test asynchronous functionality

## Development

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

### Pre-commit Hooks

1. Install pre-commit:
```bash
pip install pre-commit
pre-commit install
```

2. Run pre-commit hooks:
```bash
pre-commit run --all-files
```

## Keyboard Shortcuts

- `Ctrl + F`: Focus search
- `Ctrl + R`: Refresh results
- `Ctrl + S`: Save current view
- `Ctrl + H`: Show/hide sidebar

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 