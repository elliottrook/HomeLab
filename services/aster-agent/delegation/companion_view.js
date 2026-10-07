/* Candidate renderer only: not loaded by live Companion, no network or storage. */
function renderDelegation(root, snapshot, requestCancel) {
  root.replaceChildren();
  const doc = root.ownerDocument;
  const add = (tag, text) => {
    const node = doc.createElement(tag);
    node.textContent = text;
    root.append(node);
    return node;
  };
  add('p', typeof snapshot.message === 'string' ? snapshot.message : 'Job status unavailable.');
  if (snapshot.state === 'completed' && typeof snapshot.reply === 'string') {
    const reply = add('pre', snapshot.reply);
    reply.style.whiteSpace = 'pre-wrap';
  }
  const total = snapshot.usage?.provider_snapshots?.total?.totalTokens;
  add('p', snapshot.usage?.status === 'reported' && Number.isSafeInteger(total) && total >= 0
    ? `Provider-reported thread total: ${total} tokens. This is not a charge or remaining allowance.`
    : 'Token usage is unavailable.');
  if (snapshot.can_request_cancel === true && typeof requestCancel === 'function') {
    const button = add('button', 'Request stop');
    button.type = 'button';
    button.onclick = async () => {
      button.disabled = true;
      try {
        await requestCancel(snapshot.id);
        add('p', 'Stop requested; waiting for confirmation.');
      } catch (_) {
        add('p', 'The stop request could not be confirmed. Check the job status.');
      }
      // Do not automatically retry or claim cancellation completed.
    };
  }
}
if (typeof module !== 'undefined') module.exports = {renderDelegation};
