import React from 'react';

interface MarkdownRendererProps {
  markdown: string;
  color?: string;
}

const headingStyles: Record<number, React.CSSProperties> = {
  1: { fontSize: '1.5rem', fontWeight: 700, margin: '1.25rem 0 0.75rem' },
  2: { fontSize: '1.25rem', fontWeight: 600, margin: '1.15rem 0 0.65rem' },
  3: { fontSize: '1.1rem', fontWeight: 600, margin: '1.05rem 0 0.55rem' },
  4: { fontSize: '1rem', fontWeight: 600, margin: '0.9rem 0 0.5rem' },
  5: { fontSize: '0.95rem', fontWeight: 600, margin: '0.75rem 0 0.45rem' },
  6: { fontSize: '0.9rem', fontWeight: 600, margin: '0.6rem 0 0.4rem' },
};

const tableWrapperStyle: React.CSSProperties = {
  overflowX: 'auto',
  margin: '0.75rem 0',
};

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  minWidth: '400px',
  fontSize: '0.85rem',
};

const tableHeaderCellStyle: React.CSSProperties = {
  border: '1px solid #cbd5f5',
  background: '#f8fafc',
  padding: '0.5rem',
  textAlign: 'left',
};

const tableCellStyle: React.CSSProperties = {
  border: '1px solid #e2e8f0',
  padding: '0.5rem',
  verticalAlign: 'top',
};

const listStyle: React.CSSProperties = {
  paddingLeft: '1.5rem',
  margin: '0.5rem 0',
};

const paragraphStyle: React.CSSProperties = {
  margin: '0.75rem 0',
  lineHeight: 1.6,
};

const renderInline = (text: string, keyPrefix: string): React.ReactNode[] => {
  const nodes: React.ReactNode[] = [];
  let remaining = text;
  let segmentIndex = 0;

  const pushText = (value: string) => {
    if (value) {
      nodes.push(
        <span key={`${keyPrefix}-text-${segmentIndex++}`}>
          {value}
        </span>,
      );
    }
  };

  while (remaining.length > 0) {
    if (remaining.startsWith('**')) {
      const end = remaining.indexOf('**', 2);
      if (end !== -1) {
        const boldText = remaining.slice(2, end);
        nodes.push(
          <strong key={`${keyPrefix}-strong-${segmentIndex++}`}>
            {boldText}
          </strong>,
        );
        remaining = remaining.slice(end + 2);
        continue;
      }
    }

    if (remaining.startsWith('*')) {
      const end = remaining.indexOf('*', 1);
      if (end !== -1) {
        const italic = remaining.slice(1, end);
        nodes.push(
          <em key={`${keyPrefix}-em-${segmentIndex++}`}>
            {italic}
          </em>,
        );
        remaining = remaining.slice(end + 1);
        continue;
      }
    }

    if (remaining.startsWith('`')) {
      const end = remaining.indexOf('`', 1);
      if (end !== -1) {
        const code = remaining.slice(1, end);
        nodes.push(
          <code
            key={`${keyPrefix}-code-${segmentIndex++}`}
            style={{
              background: '#edf2f7',
              padding: '0.125rem 0.3rem',
              borderRadius: '0.25rem',
              fontSize: '0.8em',
            }}
          >
            {code}
          </code>,
        );
        remaining = remaining.slice(end + 1);
        continue;
      }
    }

    const nextSpecialIndex = (() => {
      const indices = [
        remaining.indexOf('**'),
        remaining.indexOf('*'),
        remaining.indexOf('`'),
      ].filter((idx) => idx >= 0);
      return indices.length ? Math.min(...indices) : -1;
    })();

    if (nextSpecialIndex === -1) {
      pushText(remaining);
      break;
    }

    if (nextSpecialIndex > 0) {
      pushText(remaining.slice(0, nextSpecialIndex));
      remaining = remaining.slice(nextSpecialIndex);
    } else {
      pushText(remaining.slice(0, 1));
      remaining = remaining.slice(1);
    }
  }

  return nodes;
};

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ markdown, color }) => {
  const lines = markdown.split(/\r?\n/);
  const elements: React.ReactNode[] = [];
  let listBuffer: string[] = [];
  let tableBuffer: string[][] = [];
  let tableCount = 0;
  let listCount = 0;

  const flushList = () => {
    if (!listBuffer.length) {
      return;
    }
    elements.push(
      <ul key={`list-${listCount++}`} style={listStyle}>
        {listBuffer.map((item, index) => (
          <li key={`list-item-${index}`} style={{ marginBottom: '0.4rem' }}>
            {renderInline(item, `list-${listCount}-item-${index}`)}
          </li>
        ))}
      </ul>,
    );
    listBuffer = [];
  };

  const isDividerRow = (cells: string[]) =>
    cells.every((cell) => /^:?[-]+:?$/.test(cell));

  const flushTable = () => {
    if (!tableBuffer.length) {
      return;
    }
    const rows = tableBuffer.map((row) =>
      row
        .map((cell) => cell.trim())
        .filter((cell, idx, arr) => !(idx === 0 && cell === '') && !(idx === arr.length - 1 && cell === '')),
    );

    let header: string[] = [];
    let bodyRows = rows;
    if (rows.length) {
      header = rows[0];
      bodyRows = rows.slice(1);
      if (bodyRows.length && isDividerRow(bodyRows[0])) {
        bodyRows = bodyRows.slice(1);
      }
    }

    elements.push(
      <div key={`table-${tableCount++}`} style={tableWrapperStyle}>
        <table style={tableStyle}>
          {header.length > 0 && (
            <thead>
              <tr>
                {header.map((cell, idx) => (
                  <th key={`th-${tableCount}-${idx}`} style={tableHeaderCellStyle}>
                    {renderInline(cell, `th-${tableCount}-${idx}`)}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {bodyRows.map((row, rowIdx) => (
              <tr key={`tr-${tableCount}-${rowIdx}`}>
                {row.map((cell, cellIdx) => (
                  <td key={`td-${tableCount}-${rowIdx}-${cellIdx}`} style={tableCellStyle}>
                    {renderInline(cell, `td-${tableCount}-${rowIdx}-${cellIdx}`)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>,
    );

    tableBuffer = [];
  };

  lines.forEach((rawLine, index) => {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      flushTable();
      elements.push(<div key={`spacer-${index}`} style={{ height: '0.5rem' }} />);
      return;
    }

    if (/^[-*_]{3,}$/.test(trimmed.replace(/\s+/g, ''))) {
      flushList();
      flushTable();
      elements.push(<hr key={`hr-${index}`} style={{ borderColor: '#e2e8f0', margin: '1rem 0' }} />);
      return;
    }

    if (trimmed.includes('|') && trimmed.split('|').length > 2) {
      tableBuffer.push(trimmed.split('|'));
      return;
    }

    flushTable();

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushList();
      const level = Math.min(headingMatch[1].length, 6);
      const content = headingMatch[2];
      elements.push(
        React.createElement(
          `h${level}`,
          {
            key: `heading-${index}`,
            style: headingStyles[level] ?? headingStyles[3],
          },
          renderInline(content, `heading-${index}`),
        ),
      );
      return;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      listBuffer.push(trimmed.replace(/^[-*]\s+/, ''));
      return;
    }

    flushList();

    elements.push(
      <p key={`paragraph-${index}`} style={paragraphStyle}>
        {renderInline(trimmed, `paragraph-${index}`)}
      </p>,
    );
  });

  flushList();
  flushTable();

  return (
    <div
      className="markdown-body"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.25rem',
        color: color ?? '#2d3748',
      }}
    >
      {elements}
    </div>
  );
};

export default MarkdownRenderer;
