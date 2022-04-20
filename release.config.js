var issueReleaseComment =
  ":tada: This ${issue.pull_request ? 'PR is included' : 'issue has been resolved'} in version ${nextRelease.version} :tada:" +
  '\n\nThis release is available on SplunkBase: [App](https://splunkbase.splunk.com/app/491/) - [Add-on](https://splunkbase.splunk.com/app/2757/)' +
  '\n\n> Posted by [semantic-release](https://github.com/semantic-release/semantic-release) bot'

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

var releaseNoteTemplate = `{{> header}}

{{#each commitGroups}}

{{#if title}}
### {{title}}

{{#each commits}}
{{> commit root=@root}}
{{/each}}
{{/if}}

{{/each}}
{{#if noteGroups}}
{{#each noteGroups}}

### ⚠ MAJOR RELEASE CHANGES

This is a major release

Splunk dashboards and searches you have created might be
affected by these changes. Please be prepared to test and
adjust any dashboards not included with the App after upgrade.

{{#each notes}}
* {{#if commit.scope}}**{{commit.scope}}:** {{/if}}{{text}}
{{/each}}
{{/each}}
{{/if}}`

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
          mainTemplate: releaseNoteTemplate,
        },
        presetConfig: {
          types: [
            { type: 'feat', section: 'Features' },
            { type: 'feature', section: 'Features' },
            { type: 'fix', section: 'Bug Fixes' },
            { type: 'perf', section: 'Performance Improvements' },
            { type: 'revert', section: 'Reverts' },
            { type: 'docs', hidden: true },
            { type: 'style', hidden: true },
            { type: 'chore', hidden: true },
            { type: 'refactor', hidden: true },
            { type: 'test', hidden: true },
            { type: 'build', hidden: true },
            { type: 'ci', hidden: true },
          ],
        },
      },
    ],
    [
      '@semantic-release/exec',
      {
        prepareCmd:
          'LOG_LEVEL=DEBUG scripts/build.sh -a app -v "${nextRelease.version}" -r "${nextRelease.channel}" && LOG_LEVEL=DEBUG scripts/build.sh -a addon -v "${nextRelease.version}" -r "${nextRelease.channel}"',
        publishCmd:
          'LOG_LEVEL=DEBUG scripts/publish.sh -a app -v "${nextRelease.version}" && LOG_LEVEL=DEBUG scripts/publish.sh -a addon -v "${nextRelease.version}"',
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

module.exports = releaseConfig
