const assert = require('node:assert/strict');
const {gridStep} = require('./focus.cjs');
let passed = 0;
function check(label, test) { test(); passed++; console.log('PASS', label); }
check('down preserves column', () => assert.equal(gridStep(1, 'down', 7, 4).index, 5));
check('up preserves column', () => assert.equal(gridStep(5, 'up', 7, 4).index, 1));
check('short row clamps, but remembers original column', () => {
  const down = gridStep(3, 'down', 7, 4);
  assert.equal(down.index, 6); assert.equal(down.column, 3);
  assert.equal(gridStep(down.index, 'up', 7, 4, down.column).index, 3);
});
check('left edge enters rail immediately', () => assert.equal(gridStep(4, 'left', 7, 4).area, 'rail'));
check('right edge enters filters without wrapping', () => assert.equal(gridStep(3, 'right', 7, 4).area, 'filters'));
check('last row down stays put', () => assert.equal(gridStep(6, 'down', 7, 4).index, 6));
check('top row up reaches hero action', () => assert.equal(gridStep(2, 'up', 7, 4).area, 'hero'));
check('empty results escape to navigation', () => assert.equal(gridStep(0, 'down', 0, 4).area, 'nav'));
check('one result has no phantom neighbour', () => assert.equal(gridStep(0, 'right', 1, 4).area, 'filters'));
check('all grid results remain in bounds', () => {
  for (let count = 1; count < 30; count++) for (let i = 0; i < count; i++)
    for (const dir of ['left', 'right', 'up', 'down']) {
      const next = gridStep(i, dir, count, 4);
      assert.ok(next.index >= 0 && next.index < count);
    }
});
console.log(`${passed} focus-model checks passed`);
