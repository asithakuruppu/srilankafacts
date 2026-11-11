"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useDeferredValue, useEffect, useId, useMemo, useRef, useState } from "react";

import { levelLabel } from "@/lib/format";
import { searchPlaces, type SearchEntry, type SearchResult } from "@/lib/search";

export default function SearchBox({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const [entries, setEntries] = useState<SearchEntry[] | null>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [failed, setFailed] = useState(false);
  const deferredQuery = useDeferredValue(query);
  const listId = useId();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const boxRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function close(event: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  async function loadIndex() {
    if (entries || failed) {
      return;
    }
    try {
      const response = await fetch("/search-index.json");
      if (!response.ok) {
        throw new Error(`Search index request failed (${response.status})`);
      }
      setEntries((await response.json()) as SearchEntry[]);
    } catch {
      setFailed(true);
    }
  }

  const results: SearchResult[] = useMemo(
    () => (entries ? searchPlaces(entries, deferredQuery) : []),
    [deferredQuery, entries],
  );

  function onKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setOpen(false);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActive((value) => Math.min(value + 1, Math.max(results.length - 1, 0)));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((value) => Math.max(value - 1, 0));
      return;
    }
    if (event.key === "Enter" && results[active]) {
      event.preventDefault();
      router.push(`/place/${results[active].i}`);
    }
  }

  return (
    <div className={`search ${compact ? "search-compact" : ""}`} ref={boxRef}>
      <label className="visually-hidden" htmlFor={`${listId}-input`}>
        Search for a place
      </label>
      <input
        id={`${listId}-input`}
        ref={inputRef}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={
          open && results[active] ? `${listId}-option-${active}` : undefined
        }
        autoComplete="off"
        placeholder="Search a place…"
        value={query}
        onFocus={() => {
          void loadIndex();
          setOpen(true);
        }}
        onChange={(event) => {
          setQuery(event.target.value);
          setActive(0);
          setOpen(true);
          void loadIndex();
        }}
        onKeyDown={onKeyDown}
      />
      {open && query.trim().length > 0 ? (
        <ul className="search-results" id={listId} role="listbox">
          {failed ? (
            <li className="search-empty">Search is unavailable. Browse the map instead.</li>
          ) : entries === null ? (
            <li className="search-empty">Loading index…</li>
          ) : results.length === 0 ? (
            <li className="search-empty">No place found for “{query}”.</li>
          ) : (
            results.map((result, index) => (
              <li
                key={result.i}
                id={`${listId}-option-${index}`}
                role="option"
                aria-selected={index === active}
                className={index === active ? "search-result is-active" : "search-result"}
                onMouseEnter={() => setActive(index)}
              >
                <Link
                  href={`/place/${result.i}`}
                  onClick={() => {
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  <span className="search-name">
                    {result.n || result.i}
                    {result.s ? <span className="search-script">{result.s}</span> : null}
                  </span>
                  <span className="search-meta">
                    {levelLabel(
                      result.l === 0
                        ? "country"
                        : result.l === 1
                          ? "province"
                          : result.l === 2
                            ? "district"
                            : result.l === 3
                              ? "ds"
                              : "gn",
                    )}
                    {result.pn ? ` · ${result.pn}` : ""}
                  </span>
                </Link>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
