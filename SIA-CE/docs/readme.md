# SIA-CE Documentation

This directory contains the MkDocs documentation for the SIA-CE integration package.

## Building the Documentation

### Prerequisites

1. Install Python 3.7+
2. Install documentation dependencies:
   ```bash
   pip install -r docs/requirements.txt
   ```

### Local Development

1. **Start the development server:**
   ```bash
   mkdocs serve
   ```
   The documentation will be available at `http://127.0.0.1:8000/`

2. **Live reload:**
   The development server automatically reloads when you make changes to the documentation files.

### Building for Production

1. **Build the static site:**
   ```bash
   mkdocs build
   ```
   This creates a `site/` directory with the static HTML files.

2. **Test the build:**
   ```bash
   python -m http.server 8000 --directory site/
   ```

## Deployment Options

### GitHub Pages

1. **Automatic deployment:**
   ```bash
   mkdocs gh-deploy
   ```
   This builds and pushes to the `gh-pages` branch.

2. **Manual deployment:**
   - Build the site: `mkdocs build`
   - Push the `site/` directory to `gh-pages` branch

### Other Platforms

- **Read the Docs**: Add `.readthedocs.yml` configuration
- **Netlify**: Deploy the `site/` directory
- **GitLab Pages**: Use CI/CD pipeline

## Documentation Structure

```
docs/
├── index.md                    # Home page
├── getting-started.md          # Installation guide
├── chemstation-api/            # ChemStation documentation
│   ├── introduction.md
│   ├── file-protocol.md
│   ├── basic-operations.md
│   ├── methods-sequences.md
│   └── troubleshooting.md
├── sia-api/                    # SIA documentation
│   ├── introduction.md
│   ├── basic-operations.md
│   ├── workflows.md
│   └── port-configuration.md
├── tutorials/                  # Step-by-step guides
│   ├── first-analysis.md
│   ├── batch-processing.md
│   └── sia-ce-integration.md
├── api-reference/              # API documentation
│   ├── chemstation.md
│   ├── sia.md
│   └── error-handling.md
└── appendix/                   # Additional resources
    ├── hardware-setup.md
    └── faq.md
```

## Writing Documentation

### Style Guide

1. **Headers**: Use ATX-style headers (`#`, `##`, etc.)
2. **Code blocks**: Use triple backticks with language identifier
3. **Links**: Relative links for internal pages
4. **Admonitions**: Use for tips, warnings, and notes

### Adding New Pages

1. Create a new `.md` file in the appropriate directory
2. Add the page to `nav` section in `mkdocs.yml`
3. Link to the new page from related pages

### Code Examples

Always test code examples before including them:

```python
# Good example - complete and runnable
from ChemstationAPI import ChemstationAPI

api = ChemstationAPI()
api.ce.load_vial_to_position(15, "inlet")
```

### Using Admonitions

```markdown
!!! tip "Best Practice"
    Always validate before operations.

!!! warning "Important"
    This operation cannot be undone.

!!! note
    Additional information for advanced users.
```

## Maintenance

### Regular Updates

1. **API changes**: Update reference documentation
2. **New features**: Add tutorials and examples
3. **Bug fixes**: Update troubleshooting guides
4. **User feedback**: Improve FAQ section

### Version Management

- Tag documentation versions with releases
- Maintain compatibility notes
- Update changelog

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make documentation changes
4. Test locally with `mkdocs serve`
5. Submit pull request

## Support

For documentation issues:
- Open an issue on GitHub
- Tag with `documentation`
- Provide specific page and section

## License

Documentation is licensed under the same terms as the main project (MIT License).