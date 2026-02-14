interface SystemControlsProps {
  onPartyModeToggle: () => void;
  onAllOff: () => void;
  onRefresh: () => void;
}

export function SystemControls({
  onPartyModeToggle,
  onAllOff,
  onRefresh,
}: SystemControlsProps) {
  return (
    <div className="system-controls">
      <button className="control-button party" onClick={onPartyModeToggle}>
        🎉 Party Mode
      </button>
      <button className="control-button all-off" onClick={onAllOff}>
        ⏻ All Off
      </button>
      <button className="control-button refresh" onClick={onRefresh}>
        🔄 Refresh
      </button>
    </div>
  );
}
