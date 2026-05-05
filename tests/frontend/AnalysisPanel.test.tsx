/**
 * tests/frontend/AnalysisPanel.test.tsx — T6.11
 *
 * NOTE: Vitest + @testing-library/react are not yet installed in this project.
 * This file documents the required test cases. To run these tests:
 *   1. npm install --save-dev vitest @testing-library/react @testing-library/user-event msw @vitejs/plugin-react
 *   2. Add "test": "vitest" to package.json scripts
 *   3. Create vitest.config.ts with jsdom environment
 *
 * Test spec (4 tests required by T6.11):
 *
 * describe('AnalysisPanel', () => {
 *
 *   test('shows skeleton while status=pending_analysis', async () => {
 *     // MSW mock: GET /api/intake/:leadId/blocks/:blockId/analysis → { status: 'pending_analysis' }
 *     // render(<AnalysisPanel leadId="lead-1" blockId="block-1-strategic" />)
 *     // expect(screen.getByTestId('analysis-skeleton')).toBeInTheDocument()
 *     // expect(screen.queryByTestId('analysis-panel')).not.toBeInTheDocument()
 *   })
 *
 *   test('renders suggestions when status=ready', async () => {
 *     // MSW mock: GET analysis → { status: 'ready', suggestions: [{ id, text, ... }], llm_output: {...} }
 *     // render(<AnalysisPanel leadId="lead-1" blockId="block-1-strategic" />)
 *     // await waitFor(() => screen.getByTestId('analysis-panel'))
 *     // expect(screen.getByTestId('suggestion-card')).toBeInTheDocument()
 *   })
 *
 *   test('action buttons dispatch mutation', async () => {
 *     // MSW mock: GET analysis → ready with one suggestion
 *     // MSW mock: POST /api/intake/:leadId/suggestions/:id/action → 200
 *     // render(...)
 *     // await waitFor(() => screen.getByTestId('btn-done'))
 *     // userEvent.click(screen.getByTestId('btn-done'))
 *     // await waitFor(() => expect(postRequestMade).toBe(true))
 *   })
 *
 *   test('polling stops when status=ready', async () => {
 *     // MSW mock: first call → pending_analysis, second call → ready
 *     // render(...)
 *     // verify refetchInterval returns false after ready
 *     // (verifiable via useBlockAnalysisPolling hook unit test)
 *   })
 *
 * })
 */

// Placeholder export to satisfy TypeScript
export {}
