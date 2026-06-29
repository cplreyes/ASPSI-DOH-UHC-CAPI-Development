-- Convert ```mermaid fenced code blocks into <pre class="mermaid"> elements
-- so mermaid.js renders them client-side in the HTML/PDF.
function CodeBlock(el)
  for _, c in ipairs(el.classes) do
    if c == "mermaid" then
      return pandoc.RawBlock("html", '<pre class="mermaid">\n' .. el.text .. '\n</pre>')
    end
  end
end
