<p align="center" style="color: #343a40">
  <h1 align="center">Deprecated: Splunk App and Add-on</h1>
</p>

⚠️ **Important Notice**: This TA and App is now deprecated and will no longer receive updates or support. For continued support and future updates, please switch to the new app supported by Splunk.

Please follow the [documentation](https://splunk.github.io/splunk-app-for-palo-alto-networks/Installationoverview/) for a migration path to use the Splunk supported
[Splunk App for Palo Alto Networks](https://splunkbase.splunk.com/app/7505).

Please follow the [documentation](https://splunk.github.io/splunk-add-on-for-palo-alto-networks/MigrationPaths/) for a migration path to use the Splunk supported [Splunk Add-on for Palo Alto Networks](https://splunkbase.splunk.com/app/7523).

___
>This monorepo contains both the App and Add-on for Splunk, including tests, release scripts, and CI/CD configuration


![CI/CD](https://github.com/PaloAltoNetworks/SplunkforPaloAltoNetworks/workflows/CI/CD/badge.svg?branch=master)
[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org/)
[![GitHub
contributors](https://img.shields.io/github/contributors/PaloAltoNetworks/SplunkforPaloAltoNetworks)](https://github.com/PaloAltoNetworks/SplunkforPaloAltoNetworks/graphs/contributors/)

### 📖 Documentation

https://splunk.paloaltonetworks.com

### ⬇️ Download

- [Splunk App on SplunkBase](https://splunkbase.splunk.com/app/491)
- [Splunk Add-on on SplunkBase](https://splunkbase.splunk.com/app/2757)

### 💬 Support

- [Troubleshooting Guide](https://splunk.paloaltonetworks.com/troubleshoot.html)
- [Ask a Question](https://answers.splunk.com/answers/ask.html?appid=491)
- [Report a bug](https://github.com/PaloAltoNetworks/SplunkforPaloAltoNetworks/issues)

### 🐛 Bugs / Issues / Feature Requests

Please open all issues, feature requests, and pull requests for the App or
Add-on here in this repository. We welcome your feedback and contributions! Let
us know how we're doing! 🙏

### 📚 App and Add-on READMEs

- [Splunk App README](SplunkforPaloAltoNetworks)
- [Splunk Add-on README](Splunk_TA_paloalto)

### 📂 File structure of this repo

- **SplunkforPaloAltoNetworks**: Official Splunk App
- **Splunk_TA_paloalto**: Official Splunk Add-on (TA)
- **.github**: CI/CD workflows
- **scripts**: Build and AppInspect validation scripts
- **demo**: Docker-based demo with sample data generator
- **test**: Test suites and test/development environments
- **addon-builder-exports**: Export of TA from Splunk Add-on Builder for future changes/upgrades
- **release.config.js**: Release configuration for CI/CD Release workflow

### 👩‍💻 Developer documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) to change or test the code or for
information on the CI/CD pipeline.
