# Novice walkthrough protocol — pending human sessions

Automated tests do not establish that explanations are understandable. No novice participant
sessions have been conducted for this release. Ask two or three researchers who know basic
Python but have little experience with unfamiliar repositories to try the following tasks.

Use a full copy of each upstream project at the revision in its walkthrough. The regression
snapshots under `tests/fixtures` omit data and modules and are not runnable research distributions.

1. Molyso: choose the existing-results task. Explain what a TSV row represents, find documented
   units and locate the file_name setting. Explain why image calibration is an earlier stage.
2. Gretel: explain what must happen before its command can run, name companion index files,
   locate the coordinate convention and distinguish output generation from biological accuracy.
3. Ef: explain what the .conf file supplies, distinguish starting from resuming a simulation,
   locate the stale run script and explain the separate plotting stage.

For each task ask the seven questions shown by the page. Record which answers were found,
where the person hesitated, terms they could not explain and any unsupported claim they inferred.
Do not prompt them toward the answer during the first attempt. Ask them to point to evidence.

Success means the researcher can state the purpose, required inputs, starting point, broad process,
next command and working folder, expected output and one important setting. They should also be
able to identify what has not been verified. Revise wording and navigation after observing failures.

Research-environment verification is a separate maintainer task. Run reviewed examples only in
deliberately prepared environments outside PyPadawan; record OS, Python, dependency versions,
commands and results. Until then the recipes remain labelled unverified.
