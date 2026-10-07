const assert = require('node:assert/strict');
const {renderDelegation} = require('./companion_view.js');
function root() {
  return {children: [], ownerDocument: {createElement(tag) {return {tag, style: {}};}},
    replaceChildren() {this.children = [];}, append(node) {this.children.push(node);}};
}
(async () => {
  let r = root();
  renderDelegation(r, {state:'completed', message:'Ready', reply:'<script>not executable</script>'});
  assert.equal(r.children[1].textContent, '<script>not executable</script>');
  assert.equal(r.children[1].innerHTML, undefined);
  assert.equal(r.children.at(-1).textContent, 'Token usage is unavailable.');
  r = root();
  renderDelegation(r, {state:'unknown', message:'Check status', reply:'partial answer', automatic_retry:false});
  assert.ok(r.children.every(n => n.tag !== 'pre' && n.tag !== 'button'));
  let sent = 0;
  r = root();
  renderDelegation(r, {id:'j',state:'running',can_request_cancel:true}, async id => {assert.equal(id,'j'); sent++;});
  const button = r.children.find(n => n.tag === 'button');
  await button.onclick();
  assert.equal(sent, 1); assert.equal(button.disabled, true);
  assert.equal(r.children.at(-1).textContent, 'Stop requested; waiting for confirmation.');
  r = root();
  renderDelegation(r, {id:'j',can_request_cancel:true}, async () => {throw Error('private detail');});
  await r.children.find(n => n.tag === 'button').onclick();
  assert.ok(r.children.at(-1).textContent.includes('could not be confirmed'));
  assert.ok(!JSON.stringify(r.children).includes('private detail'));
  r = root();
  renderDelegation(r,{usage:{status:'reported',provider_snapshots:{total:{totalTokens:15}}}});
  assert.ok(r.children.at(-1).textContent.includes('not a charge'));
  console.log('5 Companion renderer scenarios passed');
})();
