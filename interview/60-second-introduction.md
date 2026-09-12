# 60-second introduction

A spoken script. Read it aloud once before the call — it is written for the
mouth, not the page: short sentences, no subordinate clauses stacked up, no
words you would not actually say.

**Target: 140 words, about 60 seconds at a normal pace.**

---

## The script

> At BP-ITCS I worked on a system that turns published law into knowledge a
> machine can actually query.
>
> The hard part wasn't putting an LLM over documents. German and EU legislation
> is published as XML in two completely different markup families, and it
> changes without telling you. Once you've pulled it apart into vectors and a
> graph for retrieval, you're holding three copies of the same law — and any of
> them can quietly drift away from the source.
>
> So the work was provenance and control. Every stored version records a hash of
> the rules that produced it. Every store has exactly one writer. And the system
> refuses to certify a law it can't independently reproduce from the publisher's
> own bytes.
>
> There are five services in that system. I built four of them — the parser, the
> loader, the control-plane API, and the operator dashboard.
>
> Alongside it I worked on the document-extraction pipeline for insurance
> paperwork, and on a chest X-ray classifier where I did the calibration and the
> explainability work.

*(178 words — trim the last paragraph if you only have 60 seconds)*

---

## Notes on delivery

- **"quietly drift away from the source"** is the line that does the work. Slow
  down on it. That phrase is the whole problem statement.
- **Say the number before they ask.** "There are five services, I built four"
  pre-empts the ownership question and costs you four seconds.
- **Stop at the end.** Do not append "…and happy to go deeper on any of that."
  Let the silence hand them the next question.
- If they look blank at "markup families", substitute: *"two completely
  different XML formats that share nothing."*

## Shorter variant — about 30 seconds, 70 words

> At BP-ITCS I built most of a system that turns published German and EU law
> into verifiable machine-readable knowledge. The interesting problem wasn't
> retrieval — it was provenance. Every stored version records a hash of the
> rules that produced it, every store has exactly one writer, and the system
> refuses to certify a law it can't reproduce from the publisher's own bytes.
> Five services; I built four.

*(71 words)*

## If they ask "what does verifiable mean?" — the 20-second follow-on

> Fourteen checks measure what we stored against what the publisher actually
> served. And the checker validates itself first: if any law we'd already
> certified stops reproducing under today's rules, nothing gets a verdict at
> all — including the law you're asking about.
