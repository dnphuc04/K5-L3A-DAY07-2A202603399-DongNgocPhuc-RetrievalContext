"""Auditable benchmark authoring record. NEVER imported by retrieval or agent."""
from collections import Counter
from datetime import datetime, timezone
import re
from .common import BASE, LOCAL, SOURCE_SHA, read, sha, write

def e(page, bbox, locator, fact):
    return {"page": page, "printed_page": page - 10, "bbox": bbox, "locator": locator, "fact": fact,
            "verification": "Read against original PDF page render, not extraction alone"}

def main():
    if (BASE / "benchmarks/freeze.json").exists():
        raise SystemExit("Benchmark already frozen; refusing overwrite")
    dev, test = [], []
    def add(split, group, question, answer, evidence):
        rows = dev if split == "dev" else test
        rows.append({"id": f"ADV-{split.upper()}-{len(rows)+1:02d}", "primary_group": group,
            "question": question, "answerable": group != "unanswerable", "expected": answer,
            "units_calculation": "As explicitly stated in expected answer; no unstated unit conversion.",
            "evidence": evidence})
    def d(g,q,a,*ev): add("dev",g,q,a,list(ev))
    def t(g,q,a,*ev): add("test",g,q,a,list(ev))
    d("table", "In Table 2.1-1, which AS9100 requirements align with Decision Analysis?",
      "Measurement, Analysis and Improvement; Analysis of Data.", e(17,[.09,.88,.91,.92],"Table 2.1-1, Decision Analysis row, AS9100 column","Both mappings required"))
    d("table", "In Table 2.2-1, what is the typical outcome for Phase D?",
      "Operations-ready system end product with supporting related enabling products.",e(19,[.68,.47,.91,.57],"Table 2.2-1, Phase D / Typical Outcomes","Operations-ready plus enabling products"))
    d("table", "According to Table 4.2-2, list the verification methods and when that metadata should be determined.",
      "Test, inspection, analysis, demonstration; determined as requirements are developed.",e(69,[.09,.73,.91,.77],"Table 4.2-2, Verification method row","Four methods and development timing"))
    d("table", "In Table 6.8-1, what must the Dissent section record when applicable?",
      "Dissent with the recommendation and how it was addressed, e.g. decision matrix or risk.",e(181,[.09,.50,.91,.54],"Table 6.8-1, row 8 Dissent","Dissent and its disposition"))
    d("diagram", "In Figure 4.1-1, which two activities start the central stakeholder-expectations process, in order?",
      "Establish list of stakeholders, then elicit stakeholder expectations.",e(56,[.32,.12,.68,.20],"Figure 4.1-1, first two yellow boxes","Sequence, not just labels"))
    d("diagram", "In Figure 4.2-1, what activity immediately precedes Establish technical requirements baseline on the left-hand vertical path?",
      "Validate technical requirements.",e(65,[.28,.38,.48,.50],"Figure 4.2-1, lower-left arrow","Validation flows to baselining"))
    d("diagram", "In Figure 6.5-1, what is the last central activity after Conduct configuration audits?",
      "Capture work products from configuration management activities.",e(155,[.38,.38,.63,.48],"Figure 6.5-1, bottom two yellow boxes","Capture follows audits"))
    d("diagram", "Using the technology-readiness ladder in Figure G.4-1, what distinguishes the environments at TRL 4 and TRL 5?",
      "TRL 4 component/breadboard validation in laboratory environment; TRL 5 in relevant environment.",e(221,[.08,.08,.92,.83],"Figure G.4-1, TRL 4 and 5 boxes","Laboratory versus relevant"))
    d("chart", "In Figure 2.5-1, what percentage of life-cycle cost is shown expended at Concept?",
      "8%.",e(23,[.09,.08,.90,.60],"Figure 2.5-1, yellow Costs Expended block / Concept","8 percent, not committed-cost curve"))
    d("chart", "In Figure 2.5-1, what are the earliest and latest labeled multipliers on the cost-to-change-design-direction arrow?",
      "3–6x at the early end; 500–1000x at the late end.",e(23,[.12,.10,.89,.39],"Figure 2.5-1, rising teal cost-to-change arrow","Multipliers, not percentages"))
    d("multi_hop", "Combine Section 3.5 and Figure G.4-1: what technology-development work is completed in Phase B, and what does TRL 6 demonstrate and in what environment?",
      "Phase B completes technology development, engineering prototyping, heritage assessments and risk mitigation. TRL 6 is a system/subsystem model or prototype demonstration in a relevant environment (ground or space).",
      e(35,[.51,.51,.92,.92],"Section 3.5 Phase B opening","Technology development/prototyping/heritage/risk mitigation"),e(221,[.08,.08,.92,.83],"Figure G.4-1, TRL 6","System/subsystem model/prototype, relevant ground or space environment"))
    d("multi_hop", "Compare Figure 4.1-1 and Figure 4.2-1: to which technical definition/decomposition process are Validated Stakeholder Expectations and Validated Technical Requirements respectively sent?",
      "Validated Stakeholder Expectations go to Technical Requirements Definition; Validated Technical Requirements go to Logical Decomposition (along with requirements/interface management recipients).",
      e(56,[.68,.11,.90,.24],"Figure 4.1-1, top-right output and recipient","Technical Requirements Definition"),e(65,[.71,.14,.90,.25],"Figure 4.2-1, top-right output and recipient","Logical Decomposition"))
    d("text", "In Section 4.1.1.2.1, how is a stakeholder defined?",
      "A group or individual affected by or having a stake in the product or project.",e(55,[.51,.78,.91,.90],"Section 4.1.1.2.1 Identify Stakeholders","Affected by or stake in product/project"))
    d("text", "In Section 4.1's discussion of Needs, Goals, and Objectives, must goals already be quantitative or measurable, and what must they still allow?",
      "Goals need not be quantitative/measurable, but must allow assessment of whether achieved.",e(59,[.51,.09,.91,.23],"Goals bullet, upper-right","Need not measurable, assess achievement"))
    d("text", "According to Appendix C's Good Requirements guidance, should requirements state WHAT is needed or HOW to provide it?",
      "WHAT is needed, not HOW to provide it.",e(207,[.09,.08,.92,.93],"Appendix C, Good Requirements / correct statements","WHAT not HOW"))
    t("table", "In Table 2.1-1, give all AS9100 requirements mapped to Technical Data Management.",
      "Control of Documents; Control of Records; Control of Design and Development Changes.",e(17,[.09,.82,.91,.87],"Table 2.1-1, Technical Data Management row","All three mappings"))
    t("table", "In Table 2.2-1, what is Phase F's purpose and when was its decommissioning/disposal plan developed?",
      "Implement the system decommissioning/disposal plan developed in Phase E and analyze returned data and any returned samples.",e(19,[.09,.61,.91,.68],"Table 2.2-1, Phase F / Purpose","Phase E plan, analysis of data and samples"))
    t("table", "In Table 4.2-2, what is the function of the Rationale metadata item?",
      "Additional information to clarify the intent of requirements at the time they were written.",e(69,[.09,.62,.91,.67],"Table 4.2-2, Rationale row","Intent at writing time"))
    t("table", "According to Table 6.8-1, what four selections need rationale in Decision Matrix Setup Rationale, and what copy is required?",
      "Criteria, options, weights, evaluation methods selected; a copy of the setup decision matrix.",e(181,[.09,.24,.91,.36],"Table 6.8-1, row 3","Four selections plus setup matrix"))
    t("table", "Using Table 2.2-1, contrast the main work in Phase C and Phase E.",
      "C completes detailed system/subsystem/operations-system design, fabricates hardware and codes software/final designs; E conducts mission, meets initial need, maintains support and implements mission operations plan.",e(19,[.09,.41,.91,.62],"Table 2.2-1, Phase C and E / Purpose","Fabrication/code vs operations/sustainment"))
    t("table", "In Table 6.8-1, how long is the Executive Summary and what two one-sentence items does it contain?",
      "Short half-page; one-sentence recommendation and one-sentence problem/issue requiring a decision.",e(181,[.09,.14,.91,.20],"Table 6.8-1, row 1","Half-page, both one-sentence items"))
    t("diagram", "In Figure 2.1-1, in which direction do requirements flow through product levels, and in which direction do realized products move?",
      "Requirements flow downward from level above to below; realized products move upward from level below to above.",e(16,[.09,.10,.91,.56],"Figure 2.1-1, green arrows and level labels","Opposite directions"))
    t("diagram", "In Figure 4.0-1, after Design Solution Definition reaches Lowest Level?, where do the Yes and No branches lead?",
      "Yes goes to Product Realization Processes; No goes through the recursive cycle back to Stakeholder Expectations.",e(54,[.09,.30,.42,.44],"Figure 4.0-1, Lowest Level diamond and outgoing arrows","Yes left to product realization; No upward recursive cycle"))
    t("diagram", "In Figure 4.4-2, list the four named activities repeated around the successive-refinement spiral in order, starting with Identify and quantify goals.",
      "Identify and quantify goals → Create concepts → Do trade studies → Select design (then repeats with increased resolution).",e(77,[.51,.10,.92,.45],"Figure 4.4-2, clockwise spiral labels","Four ordered labels"))
    t("diagram", "In Figure 6.5-2, name all five elements of Configuration Management.",
      "Configuration Planning and Management; Configuration Identification; Configuration Change Management; Configuration Status Accounting; Configuration Verification.",e(155,[.18,.71,.84,.91],"Figure 6.5-2, five bottom boxes","Five elements, not activities from Figure 6.5-1"))
    t("diagram", "In Figure 6.8-2, where does the Yes branch from Is the ranking/comparison robust? go?",
      "Deliberation and Recommending a Decision Alternative.",e(176,[.65,.15,.91,.33],"Figure 6.8-2, robust diamond / Yes arrow","Directly to deliberation/recommendation"))
    t("chart", "Read the yellow Costs Expended blocks in Figure 2.5-1: what percentage is shown for Design, rather than on the committed-cost curve?",
      "15%.",e(23,[.09,.08,.90,.60],"Figure 2.5-1, Design yellow block","15 percent, cost expended"))
    t("chart", "Read Figure 2.5-1: what percentage of Costs Expended is shown at Develop?",
      "20%.",e(23,[.09,.08,.90,.60],"Figure 2.5-1, Develop yellow block","20 percent, not 90 percent committed"))
    t("chart", "Read Figure 2.5-1: what percentage of Costs Expended is shown at Prod/Test?",
      "50%.",e(23,[.09,.08,.90,.60],"Figure 2.5-1, Prod/Test yellow block","50 percent"))
    t("chart", "In Figure 4.4-3, what are the x- and y-axis quantities and how are their units described?",
      "X: life-cycle cost expressed in constant dollars. Y: some aspect of effectiveness expressed in quantitative units.",e(81,[.09,.08,.49,.44],"Figure 4.4-3, axis labels","Cost constant dollars; effectiveness quantitative units"))
    t("chart", "In Figure 4.4-3, what do dashed lines represent and in which direction is cost-effectiveness higher?",
      "Constant cost-effectiveness values; higher toward upper left.",e(81,[.09,.08,.49,.50],"Figure 4.4-3, dashed lines / explanatory note","Constant values, upper-left direction"))
    t("multi_hop", "Using the PDR and CDR rows of Table 6.7-1, compare their timing and the named design baseline approved on successful completion.",
      "PDR near completion of Phase B, last Formulation review, approves design-to baseline; CDR during Phase C approves build-to baseline (with production and verification plans).",
      e(171,[.09,.59,.91,.81],"Table 6.7-1, PDR row / Timing and Results","End B; design-to"),e(172,[.09,.14,.91,.33],"Table 6.7-1 continuation, CDR row","During C; build-to"))
    t("multi_hop", "Combine Table 2.2-1 and the SIR row of Table 6.7-1: what work does Phase D perform and when must SIR occur relative to that phase?",
      "D assembles/integrates hardware, software and humans, verifies system requirements, launches/prepares operations; SIR at end Phase C before Phase D begins.",
      e(19,[.09,.47,.91,.57],"Table 2.2-1, Phase D Purpose","Assembly/integration/test/launch/preparation"),e(172,[.09,.53,.91,.73],"Table 6.7-1, SIR Timing","End C before D"))
    t("multi_hop", "Combine Table 4.2-2 and Methods of Verification: which metadata item records the system/subsystem/element hierarchy of verification, and which verification method uses models when a prototype is unavailable?",
      "Verification level; Analysis (mathematical/analytical models or simulations when prototype not available).",
      e(69,[.09,.79,.91,.84],"Table 4.2-2, Verification level","Hierarchy level"),e(103,[.09,.08,.91,.55],"Methods of Verification, Analysis","Analytical models when prototype unavailable"))
    t("multi_hop", "Combine Figure G.4-1 and Table 2.2-1: what is TRL 9's demonstration criterion, and which named phase conducts the mission and maintains support?",
      "TRL 9 actual system flight proven through successful mission operations; Phase E Operations and Sustainment conducts mission and maintains support.",
      e(221,[.08,.08,.92,.83],"Figure G.4-1, TRL 9","Flight proven successful mission operations"),e(19,[.09,.56,.91,.62],"Table 2.2-1, Phase E","Operations and Sustainment"))
    t("text", "In Methods of Verification, distinguish Demonstration from Test in terms of data gathering and conditions.",
      "Demonstration shows basic capability without detailed data gathering; Test uses detailed data under controlled conditions to verify requirement compliance.",e(103,[.09,.08,.91,.93],"Methods of Verification, Demonstration and Test bullets","Basic/no detailed data vs detailed/controlled"))
    t("text", "In Methods of Validation, which method is identified as most resource-intensive, and does it validate stakeholder expectations or merely verify requirements?",
      "Test is most resource-intensive; validates stakeholder expectations (as opposed to verification against requirements).",e(111,[.09,.08,.91,.93],"Methods of Validation, Test bullet","Resource-intensive validation against expectations"))
    t("text", "According to Appendix C.1, what do shall, will, and should denote?",
      "Shall: requirement; will: facts or declaration of purpose; should: goal.",e(207,[.09,.08,.92,.50],"Appendix C.1 Use of Correct Terms","Three distinct modalities"))
    t("text", "In the Phase B discussion, above which life-cycle-cost threshold is the commitment made with Congress and OMB, and what is that commitment called?",
      "Life-cycle cost greater than $250M; Agency Baseline Commitment (ABC).",e(35,[.51,.75,.92,.93],"Section 3.5 Phase B, cost commitment paragraph","Strictly greater than $250M; ABC"))
    # Closely related but missing exact mandated numbers; checked over full corpus.
    for split, question, terms, section in [
      ("dev","What exact universal maximum probability of catastrophic risk must every NASA project meet at PDR in this handbook?",["catastrophic","probability","PDR"],"6.4 risk management; 6.7 reviews"),
      ("dev","What mandatory word count must every Concept of Operations document contain?",["word count","ConOps","Concept of Operations"],"4.1 and Appendix S ConOps"),
      ("dev","What universal minimum number of stakeholders must each NASA project interview?",["minimum number","stakeholders","interview"],"4.1 stakeholder expectations"),
      ("test","For all NASA missions, what single mandatory random-vibration qualification level in g RMS does this handbook specify?",["vibration","RMS","qualification"],"5.3 verification and test facilities"),
      ("test","What exact mandatory Monte Carlo sample count must all decision analyses use?",["Monte Carlo","sample count","samples"],"6.8 Decision Analysis"),
      ("test","What single annual license price in USD does the handbook give for NASA's configuration-management software?",["license","price","software"],"6.5 Configuration Management"),
      ("test","Which single programming language does the handbook mandate for every flight-software implementation?",["programming language","flight software","implementation"],"5.1 Product Implementation"),
      ("test","What exact universal number of years must every configuration-status accounting record be retained?",["retention","retained","years"],"6.5 CM and 6.6 Technical Data Management"),
      ("test","What fixed maximum dry mass in kilograms does the handbook prescribe for every lunar lander design?",["dry mass","lunar","lander"],"4.1 lunar sortie example")]:
        add(split,"unanswerable",question,"Abstain: insufficient evidence for the requested universal value/mandate.",
            [{"absence_check": {"terms": terms, "related_sections": section,
                "method": "Case-insensitive phrase scan over all 297 native-text pages; inspect related source sections. Related qualitative guidance/examples do not establish the requested universal constant.",
                "reason": "No evidence supports the exact universal mandate/value; do not substitute a mission example or external knowledge."}}])
    for split, rows in (("dev",dev),("test",test)):
        write(BASE / f"benchmarks/{split}.gold.json", rows)
        write(BASE / f"benchmarks/{split}.inputs.json", [{"id":q["id"],"question":q["question"]} for q in rows])
    pages = read(LOCAL / "index.json")
    absence = [{"id": q["id"], "term_hits": {term: [p["page"] for p in pages if term.casefold() in p["text"].casefold()]
        for term in q["evidence"][0]["absence_check"]["terms"]}} for q in dev+test if not q["answerable"]]
    write(BASE / "benchmarks/absence_checks.json", absence)
    files = sorted((BASE / "benchmarks").glob("*.json"))
    write(BASE / "benchmarks/freeze.json", {"frozen_at":datetime.now(timezone.utc).isoformat(),
        "source_sha256":SOURCE_SHA, "before_experiments":True,
        "groups":{s:dict(Counter(q["primary_group"] for q in rows)) for s,rows in (("dev",dev),("test",test))},
        "files_sha256":{str(p.relative_to(BASE)):sha(p) for p in files},
        "notes":"English source-aligned questions; Vietnamese answers. No retrieval/model experiments before this freeze. Five chart test questions cover two quantitative figures; distinct facts from dev; limited visual diversity disclosed."})
    print("Frozen 18 dev and 30 test before retrieval/model experiments")

if __name__ == "__main__":
    main()
