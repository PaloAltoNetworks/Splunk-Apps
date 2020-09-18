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

module.exports = {
  plugins: [
    '@semantic-release/commit-analyzer',
    [
      '@semantic-release/release-notes-generator',
      {
        preset: 'conventionalcommits',
        writerOpts: {
          commitPartial: commitTemplate,
        },
      },
    ],
    [
      '@semantic-release/exec',
      {
        prepareCmd: 'DEBUG=true scripts/set-version.sh ${nextRelease.version} && scripts/build.sh -a app && scripts/build.sh -a addon',
        publishCmd: 'DEBUG=true scripts/publish.sh -a app && DEBUG=true scripts/publish.sh -a addon',
      },
    ],
    [
      '@semantic-release/git',
      {
        assets: [
          'SplunkforPaloAltoNetworks/default/app.conf',
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
