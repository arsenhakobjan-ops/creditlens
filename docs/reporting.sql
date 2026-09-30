-- Run against creditlens.db after evaluating some synthetic cases.
-- These queries use SQLite JSON functions.
SELECT json_extract(result, '$.decision') AS decision, COUNT(*) AS cases,
       ROUND(AVG(json_extract(result, '$.dti_percent')), 2) AS average_dti
FROM evaluations GROUP BY decision;

SELECT id, created_at, json_extract(inputs, '$.amount') AS requested_amount,
       json_extract(result, '$.reasons') AS decision_drivers
FROM evaluations WHERE json_extract(result, '$.decision') = 'REVIEW'
ORDER BY id DESC;

SELECT json_extract(result, '$.policy_version') AS policy, COUNT(*) AS evaluations
FROM evaluations GROUP BY policy;
