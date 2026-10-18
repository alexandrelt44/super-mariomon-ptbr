-- Remote control: reads key names from CMD (one batch per write, space
-- separated, "WAIT" = 30 idle frames, SAVESTATE/LOADSTATE = slot 1,
-- DUMPWRAM = EWRAM to ewram.bin, KEY*N = hold N frames), presses each for 6 frames with a
-- 24-frame gap, then saves the screen to SHOT and touches DONE.
local DIR = os.getenv("MARIOMON_REMOTE_DIR") or "/tmp/mariomon-remote"
local CMD, SHOT, DONE = DIR .. "/cmd.txt", DIR .. "/cur.png", DIR .. "/done.txt"
local queue, timer, holding = {}, 0, nil
local tick = 0
callbacks:add("frame", function()
  tick = tick + 1
  if timer > 0 then
    timer = timer - 1
    if timer == 24 and holding then emu:clearKey(holding); holding = nil end
    if timer == 0 and #queue == 0 then
      emu:screenshot(SHOT)
      local f = io.open(DONE, "w"); f:write(tostring(tick)); f:close()
    end
    return
  end
  if #queue > 0 then
    local k = table.remove(queue, 1)
    local name, frames = k:match("^(%u+)%*(%d+)$")
    timer = 30
    if k == "SAVESTATE" then emu:saveStateSlot(1)
    elseif k == "LOADSTATE" then emu:loadStateSlot(1)
    elseif k == "DUMPWRAM" then
      local f = io.open(SHOT:gsub("cur.png$", "ewram.bin"), "wb")
      f:write(emu:readRange(0x02000000, 0x40000)); f:close()
    elseif name then
      -- KEY*N holds the key for N frames (walking needs ~16 per tile)
      holding = C.GBA_KEY[name]; emu:addKey(holding)
      timer = tonumber(frames) + 24
    elseif k ~= "WAIT" then holding = C.GBA_KEY[k]; emu:addKey(holding) end
    return
  end
  if tick % 10 == 0 then
    local f = io.open(CMD, "r")
    if f then
      local s = f:read("a"); f:close(); os.remove(CMD)
      for w in s:gmatch("%S+") do table.insert(queue, w) end
    end
  end
end)
console:log("remote pronto")
