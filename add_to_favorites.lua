local utils = require 'mp.utils'

local playlist_path = utils.join_path(os.getenv("HOME"), "Documents/pl/favorites.m3u")

function toggle_favorite()
    local path = mp.get_property("path")
    if not path then
        mp.osd_message("No file playing")
        return
    end

    local lines = {}
    local found = false

    local file = io.open(playlist_path, "r")
    if file then
        for line in file:lines() do
            if line == path then
                found = true
            else
                table.insert(lines, line)
            end
        end
        file:close()
    end

    if found then
        file = io.open(playlist_path, "w")
        for _, line in ipairs(lines) do
            file:write(line .. "\n")
        end
        file:close()
        mp.osd_message("Removed from favorites!")
    else
        file = io.open(playlist_path, "a")
        if file then
            file:write(path .. "\n")
            file:close()
            mp.osd_message("Added to favorites!")
        else
            mp.osd_message("Failed to open favorites.m3u")
        end
    end
end

mp.add_key_binding("f", "toggle-favorite", toggle_favorite)
