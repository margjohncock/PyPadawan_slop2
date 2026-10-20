# Novice-researcher walkthrough protocol

Status: **not yet conducted with human participants**. Automated tests are not a
substitute for the two or three novice researchers requested in the plan.

Recruit two or three researchers who have used basic Python for data analysis
but are unfamiliar with repository setup. Obtain their agreement to a 20-minute
session. Use the bundled teaching projects, without private research data. A
facilitator can read the following introduction:

“Your supervisor has sent you a repository that may help with your research.
Use this page to decide what it does and how you would try its example. Think
aloud when something is confusing. We are evaluating the page, not your ability.”

## Tasks

Start with `csv_analysis`. Ask the participant to use the page to answer:

1. What research task does this example support? Where does that explanation come from?
2. What do the input rows and columns represent? Which units are documented?
3. Which file and functions would you read first?
4. What happens between reading the data and saving the output? Is this a verified execution trace?
5. Where would you type the commands? Which folder and Python environment would they use?
6. What result would you compare with? Has PyPadawan verified that result by running the upload?
7. Which settings select the input and output files? What defaults are given?

Then show `undocumented_script`: can the participant identify that scientific
purpose and a launch command have not been established? Finally show
`ambiguous_setup`: can they identify that an environment route still needs choosing?

No participant needs to install or execute an uploaded project to complete these
tasks. Use the author-maintained fixture if a separate local run is desired.

## Record and improve

For each task, record the answer, evidence located, time, help needed and unfamiliar
words. Do not collect sensitive personal information. Note especially confusion
between documentation, source observations and missing information.

The release review should check that each participant can find answers or identify
specific gaps for all seven tasks. Any recurring misunderstanding about execution,
units, expected outputs or environment selection should trigger a wording or
navigation change and a repeat of the affected tasks.

| Session | Date | Tasks needing help | Observed confusion | Follow-up change |
| --- | --- | --- | --- | --- |
| Participant 1 | Pending | | | |
| Participant 2 | Pending | | | |
| Participant 3 (optional) | Pending | | | |
