import React from "react";

// Small, safe Markdown renderer for assistant replies (no HTML injection).
// Supports headings, bullet/numbered lists, paragraphs, rules, **bold**, *italic*,
// `code`, and evidence citations like [E3] / [E3, E7], which render as clickable chips.

const INLINE = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|\[E\d+(?:\s*,\s*E\d+)*\])/g;

function Inline({ text, citations, onCite }) {
  const parts = text.split(INLINE).filter((p) => p !== "");
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i}>
          <Inline text={part.slice(2, -2)} citations={citations} onCite={onCite} />
        </strong>
      );
    }
    if (/^\[E\d/.test(part)) {
      const ids = part.slice(1, -1).split(/\s*,\s*/);
      return (
        <span key={i} className="tm-cites">
          {ids.map((id) => (
            <button
              type="button"
              key={id}
              className={"tm-cite" + (citations && !citations[id] ? " tm-cite-unknown" : "")}
              title={(citations && citations[id]) || "Evidence from the class data"}
              onClick={() => onCite && onCite(id)}
            >
              {id}
            </button>
          ))}
        </span>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) return <code key={i}>{part.slice(1, -1)}</code>;
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) return <em key={i}>{part.slice(1, -1)}</em>;
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

function toBlocks(text) {
  const blocks = [];
  let paragraph = [];
  let list = null;
  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: "p", text: paragraph.join(" ") });
    paragraph = [];
  };
  const flushList = () => {
    if (list) blocks.push(list);
    list = null;
  };

  text.split(/\r?\n/).forEach((raw) => {
    const line = raw.replace(/\s+$/, "");
    const heading = line.match(/^\s*#{1,6}\s+(.*)$/);
    const bullet = line.match(/^(\s*)[-*•]\s+(.*)$/);
    const numbered = line.match(/^(\s*)\d+[.)]\s+(.*)$/);

    if (!line.trim()) {
      flushParagraph();
      flushList();
    } else if (/^\s*(---+|\*\*\*+)\s*$/.test(line)) {
      flushParagraph();
      flushList();
      blocks.push({ type: "hr" });
    } else if (heading) {
      flushParagraph();
      flushList();
      blocks.push({ type: "h", text: heading[1] });
    } else if (bullet || numbered) {
      flushParagraph();
      const [, indent, item] = bullet || numbered;
      const type = bullet ? "ul" : "ol";
      if (!list || list.type !== type) {
        flushList();
        list = { type, items: [] };
      }
      list.items.push({ text: item, nested: indent.length >= 2 });
    } else if (list && /^\s{2,}/.test(line)) {
      list.items[list.items.length - 1].text += " " + line.trim();
    } else {
      flushList();
      paragraph.push(line.trim());
    }
  });
  flushParagraph();
  flushList();
  return blocks;
}

export default function Markdown({ text, citations, onCite }) {
  return toBlocks(text || "").map((block, i) => {
    if (block.type === "hr") return <hr key={i} />;
    if (block.type === "h")
      return (
        <div key={i} className="tm-heading">
          <Inline text={block.text} citations={citations} onCite={onCite} />
        </div>
      );
    if (block.type === "p")
      return (
        <p key={i}>
          <Inline text={block.text} citations={citations} onCite={onCite} />
        </p>
      );
    const List = block.type;
    return (
      <List key={i}>
        {block.items.map((item, j) => (
          <li key={j} className={item.nested ? "tm-nested" : undefined}>
            <Inline text={item.text} citations={citations} onCite={onCite} />
          </li>
        ))}
      </List>
    );
  });
}
