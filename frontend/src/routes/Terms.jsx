import React from "react";

export default function Terms() {
  return (
    <div className="page-container">
      <h1 className="triage-meaning" style={{ fontSize: "var(--font-size-2xl)", fontWeight: 700 }}>
        Terms of Service
      </h1>

      <p className="page-intro">
        Please read these terms carefully before using the AIRA clinical guidelines assistant.
      </p>

      <section className="step-card">
        <h2 className="step-title">Not Medical Advice or Diagnosis</h2>
        <p className="step-description">
          AIRA provides informational navigation of published Indian government clinical guidelines (ICMR, MOHFW). It does not provide medical diagnoses, treatment plans, drug prescriptions, or medication dosages. Always consult a qualified physician or healthcare provider for medical decisions.
        </p>
      </section>

      <section className="step-card">
        <h2 className="step-title">Emergency Situations</h2>
        <p className="step-description">
          AIRA is not intended for emergency triage or acute resuscitation. If you experience severe chest pain, sudden weakness, breathing difficulty, severe bleeding, or suspect a medical emergency, call 112 or visit the nearest hospital emergency department immediately.
        </p>
      </section>

      <section className="step-card">
        <h2 className="step-title">Scope of Coverage</h2>
        <p className="step-description">
          AIRA covers 15 specific adult outpatient conditions referenced from ICMR Standard Treatment Workflows. It does not provide pediatric guidance, surgical triage, or comprehensive inpatient treatment protocols.
        </p>
      </section>

      <section className="step-card">
        <h2 className="step-title">Limitation of Liability</h2>
        <p className="step-description">
          AIRA and its contributors provide this service on an as-is basis for informational support. We make reasonable efforts to verify citations against authoritative sources, but do not guarantee clinical accuracy for individual patient situations.
        </p>
      </section>
    </div>
  );
}
