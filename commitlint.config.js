module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',      // new capability
        'fix',       // bug fix
        'docs',      // docs only (README, ADR, runbooks, diagrams)
        'style',     // formatting, no code-meaning change
        'refactor',  // neither fixes a bug nor adds a feature
        'perf',      // performance
        'test',      // tests
        'build',     // build system / deps
        'ci',        // CI config (.gitlab-ci.yml, pipelines)
        'chore',     // housekeeping
        'revert',    // reverts a previous commit
        'demo',      // custom: planted-vulnerability / attack-scenario commits
        'security',  // custom: security control / hardening changes
      ],
    ],
    'body-max-line-length': [0, 'always', Infinity],
    'footer-max-line-length': [0, 'always', Infinity],
  },
};
