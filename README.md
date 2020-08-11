<p align="center" style="color: #343a40">
  <img src=".github/splunk-logo.png" alt="Splunk" height="120">
  <h1 align="center">Splunk App and Add-on</h1>
</p>
<h3 align="center" style="font-size: 1.2rem;">The official Palo Alto Networks Splunk App and Add-on</h3>

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

#### Test changes in your branch

Requires docker and docker-compose

```shell
cd test/standalone-with-data
docker-compose up -d --build
```

This takes several minutes the first time you run it. After a while, point your
browser to http://localhost:8001 for a Splunk server with sample logs you can
use to test the changes in your branch. After the Splunk server comes up, it
could take several more minutes for logs to show up on the server.

To save time in future tests, use `docker-compose stop` and
`docker-compose start` to turn the server off and on between testing
sessions. To completely reset the test environment type
`docker-compose down -v && docker-compose up -d --build`.

Note: Any change you make to the App or Add-on will show up immediately in
Splunk. There is a second docker container that monitors the App/Add-on
directories and reloads them in Splunk when a change is detected.

#### Publish a new release

Requires node and semantic-release npm package

```shell
# Test the release process on develop
semantic-release --dry-run --no-ci --branches=develop

# Verify in the output that the next version is set correctly
# and the release note is generated correctly

# Merge develop to master and push
git checkout master
git merge develop
git push origin master

# At this point, GitHub Actions is testing the release
# then building it for publication

# There is a manual step here. You'll have to get the build
# from the GitHub Actions artifacts and publish it on SplunkBase
# manually. We can automate this when the SplunkBase API is more mature.

# Now, sync your local with the remote to pull the new
# commits made by the release bot.
git pull origin master
git checkout develop
git merge master
git push origin develop
```