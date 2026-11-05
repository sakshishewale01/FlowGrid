import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const readSource = (relativePath) => fs.readFileSync(
  new URL(`../src/${relativePath}`, import.meta.url),
  'utf8',
);

test('Live delay-risk panel uses the authenticated analytics endpoint', () => {
  const apiSource = readSource('api/analytics.js');
  const hookSource = readSource('hooks/useDashboardData.js');
  const panelSource = readSource('components/AiInsightPanel.jsx');

  assert.match(apiSource, /\/api\/v1\/analytics\/delay-risk/);
  assert.match(hookSource, /analyticsApi\.getDelayRisk/);
  assert.match(panelSource, /Rule-based, explainable risk calculations/);
  assert.match(panelSource, /Rule-based, not a calibrated probability/);
});

test('Live delay-risk panel has loading, empty, and error states', () => {
  const panelSource = readSource('components/AiInsightPanel.jsx');

  assert.match(panelSource, /loading \? '\.\.\.'/);
  assert.match(panelSource, /Zero active shipments currently at delay risk/);
  assert.match(panelSource, /Delay-risk data unavailable/);
});

test('Fabricated predictor copy is absent from dashboard source', () => {
  const source = [
    readSource('App.jsx'),
    readSource('components/AiInsightPanel.jsx'),
    readSource('pages/AnalyticsPage.jsx'),
    readSource('pages/RescueCenterPage.jsx'),
  ].join('\n');
  const oldPrecision = ['96', '.4%'].join('');
  const oldTrainingClaim = ['42', 'k historical'].join('');

  assert.equal(source.includes(oldPrecision), false);
  assert.equal(source.includes(oldTrainingClaim), false);
});
