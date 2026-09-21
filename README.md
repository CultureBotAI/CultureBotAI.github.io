# CultureBotAI Website

This is the source code for the CultureBotAI organization website, built with Jekyll and hosted on GitHub Pages.

## Website URL
[https://culturebotai.github.io](https://culturebotai.github.io)

## Local Development

### Prerequisites
- Ruby (version 2.7 or higher)
- Bundler gem

### Setup
```bash
# Clone the repository
git clone https://github.com/CultureBotAI/CultureBotAI.github.io.git
cd CultureBotAI.github.io

# Install dependencies
bundle install

# Serve the site locally
bundle exec jekyll serve
```

The site will be available at `http://localhost:4000`.

## Site Structure

- `_config.yml` - Jekyll configuration
- `index.md` - Homepage
- `about.md` - About page with PI and lab information
- `research.md` - Research focus areas and projects
- `resources.md` - Tools, databases, and kg-microbe information
- `publications.md` - Papers, preprints, and presentations

## Content Updates

Content is written in Markdown and automatically deployed via GitHub Pages when pushed to the `main` branch.

## X-Mech terminology

Use **autonomous knowledge factory** (plural: **autonomous knowledge factories**)
as the official label for an X-Mech. Each X-Mech curates, validates, and connects
scientific evidence to enable discovery, with human oversight. Use **knowledge
base** for its stored records and **knowledge graph** for graph representations
or outputs. Preserve publication titles and source quotations.

The X-Mech suite page is generated; edit its sources in `_fleet/` and rebuild
following [`_fleet/README.md`](_fleet/README.md).

## Contributing

For content updates or corrections, please:
1. Fork the repository
2. Make your changes
3. Submit a pull request

## Contact

For questions about the website or content updates:
- Email: [mjoachimiak@lbl.gov](mailto:mjoachimiak@lbl.gov)
- GitHub: [CultureBotAI Organization](https://github.com/CultureBotAI)

## License

This website content is licensed under [MIT License](LICENSE).