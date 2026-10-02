# Isolated legacy components

These components were found unused by the Phase 0 audit and are retained here
for reference rather than compiled into the application. The current dashboard
uses the corresponding components in `src/components/`. `ReplaySystemModal`
contains synthetic replay frames and is not connected to persisted simulation
history; `IncidentInvestigationModal` is an unwired feature, so both remain
isolated instead of being presented as active functionality.
