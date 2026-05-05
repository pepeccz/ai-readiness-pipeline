/**
 * tests/frontend/DeepReviewPanel.test.tsx — T7.8
 *
 * Vitest + Testing Library spec for DeepReviewPanel.
 * NOTE: Vitest is NOT installed in this project. This file documents the
 * expected component behaviour to guide manual testing and future CI setup.
 *
 * Scenarios covered:
 *  1. Renders empty state when no branches
 *  2. Renders branch list with status badges
 *  3. Edit mode: clicking "Editar" shows textarea for each question
 *  4. Saving edited questions calls PATCH /api/intake/{lead_id}/deep/{branch_id}
 *  5. "Enviar al cliente" calls POST /api/intake/{lead_id}/deep/{branch_id}/send
 *  6. After send: branch status shows "sent_to_client"
 *  7. Questions in pending_generation show skeleton loader
 */

// import { render, screen, fireEvent, waitFor } from "@testing-library/react";
// import { DeepReviewPanel } from "../../frontend/src/intake/DeepReviewPanel";
// import { describe, it, expect, vi } from "vitest";

// describe("DeepReviewPanel", () => {
//   it("renders empty state when branches array is empty", () => {
//     render(<DeepReviewPanel leadId="l1" branches={[]} />);
//     expect(screen.getByText(/no hay ramas/i)).toBeInTheDocument();
//   });

//   it("renders all branches with correct status", () => {
//     const branches = [
//       { id: "b1", branch_id: "strategic", status: "pending_review", generated_questions: [] },
//       { id: "b2", branch_id: "governance", status: "sent_to_client", generated_questions: [] },
//     ];
//     render(<DeepReviewPanel leadId="l1" branches={branches} />);
//     expect(screen.getByText("strategic")).toBeInTheDocument();
//     expect(screen.getByText("sent_to_client")).toBeInTheDocument();
//   });

//   it("shows edit fields when 'Editar' clicked", async () => {
//     const branch = {
//       id: "b1",
//       branch_id: "strategic",
//       status: "pending_review",
//       generated_questions: [{ id: "dq1", text: "Pregunta original" }],
//     };
//     render(<DeepReviewPanel leadId="l1" branches={[branch]} />);
//     fireEvent.click(screen.getByText("Editar"));
//     expect(screen.getByDisplayValue("Pregunta original")).toBeInTheDocument();
//   });

//   it("calls PATCH on save with updated questions", async () => {
//     const mockPatch = vi.fn().mockResolvedValue({ ok: true });
//     // inject mock fetch or api layer
//     const branch = { id: "b1", branch_id: "data", status: "pending_review", generated_questions: [] };
//     render(<DeepReviewPanel leadId="l1" branches={[branch]} />);
//     fireEvent.click(screen.getByText("Editar"));
//     fireEvent.click(screen.getByText("Guardar"));
//     await waitFor(() => expect(mockPatch).toHaveBeenCalled());
//   });

//   it("calls POST send on 'Enviar al cliente'", async () => {
//     const mockSend = vi.fn().mockResolvedValue({ signed_url: "http://..." });
//     const branch = { id: "b1", branch_id: "strategic", status: "pending_review", generated_questions: [] };
//     render(<DeepReviewPanel leadId="l1" branches={[branch]} />);
//     fireEvent.click(screen.getByText("Enviar al cliente"));
//     await waitFor(() => expect(mockSend).toHaveBeenCalled());
//   });
// });

export {};
