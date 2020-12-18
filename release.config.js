var currentBranch = process.env.GITHUB_REF
if (currentBranch) {
  currentBranch = currentBranch.replace('refs/heads/', '')
}

var issueReleaseComment =
  ":tada: This ${issue.pull_request ? 'PR is included' : 'issue has been resolved'} in version ${nextRelease.version} :tada:" +
  '\n\nThis release is available on SplunkBase: [App](https://splunkbase.splunk.com/app/491/) - [Add-on](https://splunkbase.splunk.com/app/2757/)' +
  '\n\n> Posted by [semantic-release](https://github.com/semantic-release/semantic-release) bot'

// Not used currently
var commitTemplate = `*{{#if scope}} **{{scope}}:**
{{~/if}} {{#if subject}}
  {{~subject}}
{{~else}}
  {{~header}}
{{~/if}}

{{~!-- commit references --}} {{#if references~}}
  -
  {{~#each references}} {{#if @root.linkReferences~}}
    {{~#if this.owner}}
      {{~this.owner}}/
    {{~/if}}
    {{~this.repository}}{{this.prefix}}{{this.issue}}
  {{~else}}
    {{~#if this.owner}}
      {{~this.owner}}/
    {{~/if}}
    {{~this.repository}}{{this.prefix}}{{this.issue}}
  {{~/if}}{{/each}}
{{~/if}}

`

// Pre-release configuration (eg. beta or alpha release)
var prereleaseConfig = {
  preset: 'conventionalcommits',
  plugins: [
    '@semantic-release/commit-analyzer',
    [
      '@semantic-release/release-notes-generator',
      {
        writerOpts: {
          commitPartial: commitTemplate,
        },
      },
    ],
    [
      '@semantic-release/exec',
      {
        prepareCmd:
          'LOG_LEVEL=DEBUG scripts/set-version.sh "${nextRelease.version}" "${nextRelease.channel}" && git add -A && git commit -m "Pre-release ${nextRelease.version}"',
        publishCmd: 'scripts/build.sh -a app && scripts/build.sh -a addon',
      },
    ],
    [
      '@semantic-release/github',
      {
        successComment: false,
        assets: [
          {path: '_build/SplunkforPaloAltoNetworks-*', label: 'SplunkforPaloAltoNetworks (App)'},
          {path: '_build/Splunk_TA_paloalto-*', label: 'Splunk_TA_paloalto (Add-on)'},
        ],
      },
    ],
  ],
}

// Config for any full release (eg. master or maintenance releases)
var releaseConfig = {
  preset: 'conventionalcommits',
  plugins: [
    '@semantic-release/commit-analyzer',
    [
      '@semantic-release/release-notes-generator',
      {
        writerOpts: {
          commitPartial: commitTemplate,
        },
      },
    ],
    [
      '@semantic-release/exec',
      {
        prepareCmd:
          'LOG_LEVEL=DEBUG scripts/set-version.sh "${nextRelease.version}" "${nextRelease.channel}"',
        publishCmd:
          'scripts/build.sh -a app && scripts/build.sh -a addon && LOG_LEVEL=DEBUG scripts/publish.sh -a app && LOG_LEVEL=DEBUG scripts/publish.sh -a addon',
      },
    ],
    [
      '@semantic-release/git',
      {
        assets: [
          'SplunkforPaloAltoNetworks/default/app.conf',
          'SplunkforPaloAltoNetworks/app.manifest',
          'SplunkforPaloAltoNetworks/README.md',
          'Splunk_TA_paloalto/default/app.conf',
          'Splunk_TA_paloalto/app.manifest',
          'Splunk_TA_paloalto/README.md',
        ],
        message:
          'chore(release): ${nextRelease.version}\n\n${nextRelease.notes}',
      },
    ],
    [
      '@semantic-release/github',
      {
        successComment: issueReleaseComment,
      },
    ],
  ],
}

var configuration
if (currentBranch === 'beta' || currentBranch === 'alpha') {
  configuration = prereleaseConfig
} else {
  configuration = releaseConfig
}

module.exports = configuration