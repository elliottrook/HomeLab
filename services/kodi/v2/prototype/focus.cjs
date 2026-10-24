/* Pure remote-navigation model, shared by the preview and Node tests. */
(function (root) {
  function gridStep(index, direction, count, columns, preferredColumn) {
    if (!Number.isInteger(count) || count < 1 || !Number.isInteger(columns) || columns < 1)
      return {area: 'nav', index: 0, column: 0};
    index = Math.max(0, Math.min(count - 1, index));
    const row = Math.floor(index / columns);
    let column = Number.isInteger(preferredColumn) ? preferredColumn : index % columns;
    if (direction === 'left') {
      if (index % columns === 0) return {area: 'rail', index, column};
      return {area: 'grid', index: index - 1, column: (index - 1) % columns};
    }
    if (direction === 'right') {
      if (index % columns === columns - 1 || index === count - 1)
        return {area: 'filters', index, column};
      return {area: 'grid', index: index + 1, column: (index + 1) % columns};
    }
    if (direction === 'up' && row === 0) return {area: 'hero', index, column};
    const nextRow = row + (direction === 'up' ? -1 : direction === 'down' ? 1 : 0);
    if (nextRow * columns >= count) return {area: 'grid', index, column};
    const next = nextRow * columns + Math.min(column, count - nextRow * columns - 1);
    return {area: 'grid', index: next, column};
  }
  const api = {gridStep};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.AsterFocus = api;
})(typeof window !== 'undefined' ? window : globalThis);
