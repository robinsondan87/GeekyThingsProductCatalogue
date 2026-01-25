<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
      const searchInput = document.getElementById("searchInput");
      const ukcaFilter = document.getElementById("ukcaFilter");
      const viewTabs = document.getElementById("viewTabs");
      const tableView = document.getElementById("tableView");
      const folderView = document.getElementById("folderView");
      const folderTitle = document.getElementById("folderTitle");
      const folderList = document.getElementById("folderList");
      const folderEmpty = document.getElementById("folderEmpty");
      const readmeDialog = document.getElementById("readmeDialog");
      const readmeContent = document.getElementById("readmeContent");
      const readmeTitle = document.getElementById("readmeTitle");
      const readmePath = document.getElementById("readmePath");
      const closeReadmeBtn = document.getElementById("closeReadmeBtn");
      const saveReadmeBtn = document.getElementById("saveReadmeBtn");
      const statusEl = document.getElementById("status");
      const logoutBtn = document.getElementById("logoutBtn");
      const table = document.getElementById("dataTable");
      const colgroup = document.getElementById("colgroup");
      const thead = table.querySelector("thead");
      const tbody = table.querySelector("tbody");
      const emptyState = document.getElementById("emptyState");

      let fileHandle = null;
      let autosaveTimer = null;
      let saveInFlight = false;
      let isDirty = false;
      let headers = [];
      let rows = [];
      const dropdownColumns = new Set([]);
      const chipColumns = new Set(["tags", "Colors", "Sizes"]);
      const listingOptions = ["Facebook", "TikTok", "Ebay", "Etsy"];
      const columnFilters = new Map();
      let sortIndex = -1;
      let sortDirection = 1;
      let columnWidths = [];
      let originalNames = [];
      const hiddenColumns = new Set([
        "id",
        "Facebook URL",
        "TikTok URL",
        "Ebay URL",
        "Etsy URL",
        "Status",
        "Cost To Make",
        "Sale Price",
        "Postage Price",
      ]);
      let viewMode = "live";

      const normalizeStatus = (value) => {
        const lowered = String(value || "").trim().toLowerCase();
        if (lowered === "draft") return "Draft";
        if (lowered === "archived") return "Archived";
        return "Live";
      };

      const normalizeUkca = (value) => {
        const lowered = String(value || "").trim().toLowerCase();
        if (lowered === "yes") return "Yes";
        if (lowered === "n/a" || lowered === "na") return "N/A";
        return "No";
      };

      const getListingsForRow = (row) => {
        const facebookUrl = row[headers.indexOf("Facebook URL")] || "";
        const tiktokUrl = row[headers.indexOf("TikTok URL")] || "";
        const ebayUrl = row[headers.indexOf("Ebay URL")] || "";
        const etsyUrl = row[headers.indexOf("Etsy URL")] || "";
        const listings = [];
        if (facebookUrl) listings.push({ name: "Facebook", url: facebookUrl });
        if (tiktokUrl) listings.push({ name: "TikTok", url: tiktokUrl });
        if (ebayUrl) listings.push({ name: "Ebay", url: ebayUrl });
        if (etsyUrl) listings.push({ name: "Etsy", url: etsyUrl });
        return listings;
      };

      const getVisibleHeaders = () => headers.filter((header) => !hiddenColumns.has(header));
      let readmeRowIndex = null;

      const parseCSV = (text) => {
        const output = [];
        let row = [];
        let value = "";
        let inQuotes = false;

        for (let i = 0; i < text.length; i += 1) {
          const char = text[i];
          const next = text[i + 1];

          if (char === '"') {
            if (inQuotes && next === '"') {
              value += '"';
              i += 1;
            } else {
              inQuotes = !inQuotes;
            }
          } else if (char === "," && !inQuotes) {
            row.push(value);
            value = "";
          } else if ((char === "\n" || char === "\r") && !inQuotes) {
            if (char === "\r" && next === "\n") {
              i += 1;
            }
            row.push(value);
            if (row.length > 1 || row[0] !== "") {
              output.push(row);
            }
            row = [];
            value = "";
          } else {
            value += char;
          }
        }

        row.push(value);
        if (row.length > 1 || row[0] !== "") {
          output.push(row);
        }

        return output;
      };

      const parseList = (value) =>
        (value || "")
          .split(",")
          .map((item) => item.trim())
          .filter((item) => item.length);

      const uniqueSorted = (items) => {
        const seen = new Map();
        items.forEach((item) => {
          const key = item.toLowerCase();
          if (!seen.has(key)) {
            seen.set(key, item);
          }
        });
        return Array.from(seen.values()).sort((a, b) => a.localeCompare(b));
      };

      const renderChipList = (items, container, onRemove) => {
        container.innerHTML = "";
        if (!items.length) {
          const empty = document.createElement("span");
          empty.className = "variant-empty";
          empty.textContent = "None added";
          container.appendChild(empty);
          return;
        }
        items.forEach((value) => {
          const chip = document.createElement("span");
          chip.className = "variant-chip";
          chip.textContent = value;
          const removeBtn = document.createElement("button");
          removeBtn.type = "button";
          removeBtn.className = "variant-remove";
          removeBtn.textContent = "×";
          removeBtn.addEventListener("click", () => onRemove(value));
          chip.appendChild(removeBtn);
          container.appendChild(chip);
        });
      };

      const addToList = (value, list) => {
        const cleaned = (value || "").trim().replace(/,+$/, "");
        if (!cleaned) return list;
        const lower = cleaned.toLowerCase();
        if (list.some((item) => item.toLowerCase() === lower)) return list;
        return uniqueSorted([...list, cleaned]);
      };

      const csvEscape = (value) => {
        if (value == null) return "";
        const stringValue = String(value);
        if (/["]|,|\n|\r/.test(stringValue)) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      };

      const toCSV = (headers, rows) => {
        const headerLine = headers.map(csvEscape).join(",");
        const rowLines = rows.map((row) => row.map(csvEscape).join(","));
        return [headerLine, ...rowLines].join("\n");
      };

      const updateStatus = () => {
        const total = rows.length;
        const visible = tbody.querySelectorAll("tr").length;
        if (!headers.length) {
          statusEl.textContent = "No file loaded.";
          return;
        }
        let suffix = "";
        if (viewMode === "b2b") suffix = " (B2B)";
        if (viewMode === "live") suffix = " (Live)";
        statusEl.textContent = `Loaded ${total} rows. Showing ${visible}.${suffix}`;
      };

      const scheduleSave = () => {
        if (!headers.length) return;
        if (viewMode === "archived" || viewMode === "draft") return;
        if (autosaveTimer) {
          clearTimeout(autosaveTimer);
        }
        isDirty = true;
        statusEl.textContent = "Changes pending...";
        autosaveTimer = setTimeout(() => {
          saveViaApi().catch(console.error);
        }, 1200);
      };

      const renderColgroup = () => {
        colgroup.innerHTML = "";
        const totalColumns = getVisibleHeaders().length + 1;
        for (let i = 0; i < totalColumns; i += 1) {
          const col = document.createElement("col");
          if (columnWidths[i]) {
            col.style.width = columnWidths[i];
          }
          colgroup.appendChild(col);
        }
      };

      const attachResizer = (th, colIndex) => {
        const resizer = document.createElement("div");
        resizer.className = "resizer";
        let startX = 0;
        let startWidth = 0;

        const onMouseMove = (event) => {
          const delta = event.clientX - startX;
          const newWidth = Math.max(90, startWidth + delta);
          columnWidths[colIndex] = `${newWidth}px`;
          renderColgroup();
        };

        const onMouseUp = () => {
          document.removeEventListener("mousemove", onMouseMove);
          document.removeEventListener("mouseup", onMouseUp);
        };

        resizer.addEventListener("mousedown", (event) => {
          startX = event.clientX;
          startWidth = th.offsetWidth;
          document.addEventListener("mousemove", onMouseMove);
          document.addEventListener("mouseup", onMouseUp);
        });

        th.appendChild(resizer);
      };

      const renderHeader = () => {
        thead.innerHTML = "";
        if (headers.length === 0) return;
        const row = document.createElement("tr");
        getVisibleHeaders().forEach((header, visibleIndex) => {
          const headerIndex = headers.indexOf(header);
          const th = document.createElement("th");
          const button = document.createElement("button");
          const indicator =
            sortIndex === headerIndex ? (sortDirection === 1 ? "▲" : "▼") : "↕";
          button.textContent = `${header} ${indicator}`;
          button.addEventListener("click", () => {
            if (sortIndex === headerIndex) {
              sortDirection *= -1;
            } else {
              sortIndex = headerIndex;
              sortDirection = 1;
            }
            renderHeader();
            renderBody();
          });
          th.appendChild(button);
          attachResizer(th, visibleIndex);
          row.appendChild(th);
        });
        const th = document.createElement("th");
        th.textContent = "Actions";
        row.appendChild(th);
        thead.appendChild(row);

        const filterRow = document.createElement("tr");
        filterRow.className = "filters";
        getVisibleHeaders().forEach((header) => {
          const colIndex = headers.indexOf(header);
          const th = document.createElement("th");
          if (header === "Listings") {
            const select = document.createElement("select");
            const options = [""].concat(listingOptions);
            options.forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value === "" ? "Any" : value;
              select.appendChild(option);
            });
            select.value = columnFilters.get(colIndex) || "";
            select.addEventListener("change", (event) => {
              const value = event.target.value;
              if (value) {
                columnFilters.set(colIndex, value);
              } else {
                columnFilters.delete(colIndex);
              }
              renderBody();
              updateStatus();
            });
            th.appendChild(select);
          } else if (dropdownColumns.has(header)) {
            const select = document.createElement("select");
            const options = ["", "Yes", "No", "N/A"];
            options.forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value === "" ? "All" : value;
              select.appendChild(option);
            });
            select.value = columnFilters.get(colIndex) || "";
            select.addEventListener("change", (event) => {
              const value = event.target.value;
              if (value) {
                columnFilters.set(colIndex, value);
              } else {
                columnFilters.delete(colIndex);
              }
              renderBody();
              updateStatus();
            });
            th.appendChild(select);
          } else {
            const input = document.createElement("input");
            input.type = "search";
            input.placeholder = `Filter ${header}`;
            input.value = columnFilters.get(colIndex) || "";
            input.addEventListener("input", (event) => {
              const value = event.target.value.trim();
              if (value) {
                columnFilters.set(colIndex, value);
              } else {
                columnFilters.delete(colIndex);
              }
              renderBody();
              updateStatus();
            });
            th.appendChild(input);
          }
          filterRow.appendChild(th);
        });
        const actionsTh = document.createElement("th");
        actionsTh.textContent = "";
        filterRow.appendChild(actionsTh);
        thead.appendChild(filterRow);
        renderColgroup();
      };

      const applyFilter = (row) => {
        const query = searchInput.value.trim().toLowerCase();
        const categoryIndex = headers.indexOf("category");
        const folderIndex = headers.indexOf("product_folder");
        const skuIndex = headers.indexOf("sku");
        const tagsIndex = headers.indexOf("tags");
        const listingsIndex = headers.indexOf("Listings");
        const statusIndex = headers.indexOf("Status");
        const statusValue = statusIndex > -1 ? (row[statusIndex] || "") : "";

        if (normalizeStatus(statusValue) === "Archived" || normalizeStatus(statusValue) === "Draft") {
          return false;
        }

        if (viewMode === "b2b" && categoryIndex > -1 && row[categoryIndex] !== "B2B") {
          return false;
        }

        if (viewMode === "live" && categoryIndex > -1 && row[categoryIndex] === "B2B") {
          return false;
        }

        if (query) {
          const combined = [
            row[categoryIndex] || "",
            row[folderIndex] || "",
            skuIndex > -1 ? row[skuIndex] || "" : "",
            tagsIndex > -1 ? row[tagsIndex] || "" : "",
            listingsIndex > -1 ? getListingsForRow(row).map((item) => item.name).join(", ") : "",
          ]
            .join(" ")
            .toLowerCase();
          return combined.includes(query);
        }

        for (const [colIndex, value] of columnFilters.entries()) {
          let cell = (row[colIndex] ?? "").toString();
          if (headers[colIndex] === "Listings") {
            cell = getListingsForRow(row).map((item) => item.name).join(", ");
            if (!cell.toLowerCase().includes(value.toLowerCase())) return false;
          } else if (headers[colIndex] === "UKCA") {
            if (normalizeUkca(cell) !== value) return false;
          } else if (dropdownColumns.has(headers[colIndex])) {
            if (cell !== value) return false;
          } else if (!cell.toLowerCase().includes(value.toLowerCase())) {
            return false;
          }
        }

        return true;
      };

      const setUkcaFilter = (value) => {
        const colIndex = headers.indexOf("UKCA");
        if (colIndex === -1) return;
        if (!value) {
          columnFilters.delete(colIndex);
        } else {
          columnFilters.set(colIndex, value);
        }
        renderBody();
        updateStatus();
      };

      const renderBody = () => {
        tbody.innerHTML = "";
        const fragment = document.createDocumentFragment();
        const indexedRows = rows.map((row, index) => ({ row, index }));
        if (sortIndex > -1) {
          indexedRows.sort((a, b) => {
            const aValue = (a.row[sortIndex] ?? "").toString().toLowerCase();
            const bValue = (b.row[sortIndex] ?? "").toString().toLowerCase();
            if (aValue < bValue) return -1 * sortDirection;
            if (aValue > bValue) return 1 * sortDirection;
            return a.index - b.index;
          });
        }
        const productFolderIndex = headers.indexOf("product_folder");
        const categoryIndex = headers.indexOf("category");
        indexedRows.forEach(({ row, index: rowIndex }) => {
          if (!applyFilter(row)) return;
          const tr = document.createElement("tr");
          tr.dataset.index = String(rowIndex);
          getVisibleHeaders().forEach((header) => {
            const colIndex = headers.indexOf(header);
            const td = document.createElement("td");
            if (header === "Listings") {
              const wrapper = document.createElement("div");
              wrapper.className = "listing-links";
              const listings = getListingsForRow(row);
              if (listings.length === 0) {
                wrapper.textContent = "—";
              } else {
                listings.forEach((item) => {
                  const link = document.createElement("a");
                  link.href = item.url;
                  link.target = "_blank";
                  link.rel = "noopener noreferrer";
                  link.textContent = item.name;
                  wrapper.appendChild(link);
                });
              }
              td.appendChild(wrapper);
            } else if (header === "UKCA") {
              const badge = document.createElement("span");
              const value = normalizeUkca(row[colIndex]);
              badge.className = `ukca-badge ${
                value === "Yes" ? "is-yes" : value === "N/A" ? "is-na" : "is-no"
              }`;
              badge.textContent = value;
              td.appendChild(badge);
            } else if (dropdownColumns.has(header)) {
              const select = document.createElement("select");
              ["No", "Yes", "N/A"].forEach((optionValue) => {
                const option = document.createElement("option");
                option.value = optionValue;
                option.textContent = optionValue;
                select.appendChild(option);
              });
              select.value = row[colIndex] || "No";
              select.addEventListener("change", (event) => {
                rows[rowIndex][colIndex] = event.target.value;
                scheduleSave();
              });
              td.appendChild(select);
            } else if (colIndex === productFolderIndex) {
              const wrapper = document.createElement("div");
              wrapper.className = "path-cell";
              const input = document.createElement("input");
              input.value = row[colIndex] ?? "";
              input.addEventListener("input", (event) => {
                rows[rowIndex][colIndex] = event.target.value;
                scheduleSave();
              });
              input.addEventListener("blur", async (event) => {
                if (viewMode !== "live") return;
                const category = rows[rowIndex][categoryIndex] || "";
                const newName = event.target.value.trim();
                const oldName = originalNames[rowIndex] || "";
                if (!category || !newName || !oldName) return;
                if (newName === oldName) return;
                try {
                  const response = await fetch("/api/rename", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      category,
                      old_name: oldName,
                      new_name: newName,
                      status: "live",
                    }),
                  });
                  const payload = await response.json();
                  if (!response.ok) {
                    rows[rowIndex][colIndex] = oldName;
                    event.target.value = oldName;
                    statusEl.textContent = payload.error || "Rename failed.";
                    return;
                  }
                  originalNames[rowIndex] = newName;
                  statusEl.textContent = "Folder renamed.";
                  setTimeout(updateStatus, 1500);
                } catch (error) {
                  console.error(error);
                  rows[rowIndex][colIndex] = oldName;
                  event.target.value = oldName;
                  statusEl.textContent = "Rename failed.";
                }
              });
              wrapper.appendChild(input);
              td.appendChild(wrapper);
            } else if (chipColumns.has(header)) {
              const wrapper = document.createElement("div");
              wrapper.className = "chip-editor";
              const listEl = document.createElement("div");
              listEl.className = "variant-list";
              const input = document.createElement("input");
              input.type = "text";
              input.className = "chip-input";
              input.placeholder = `Add ${header === "tags" ? "tag" : header.toLowerCase()}`;
              let current = uniqueSorted(parseList(row[colIndex] || ""));

              const setList = (next) => {
                current = uniqueSorted(next);
                rows[rowIndex][colIndex] = current.join(", ");
                scheduleSave();
                renderChipList(current, listEl, removeItem);
              };

              const removeItem = (value) => {
                setList(current.filter((item) => item !== value));
              };

              renderChipList(current, listEl, removeItem);

              input.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === ",") {
                  event.preventDefault();
                  const next = addToList(input.value, current);
                  if (next !== current) {
                    setList(next);
                  }
                  input.value = "";
                }
              });

              input.addEventListener("blur", () => {
                const next = addToList(input.value, current);
                if (next !== current) {
                  setList(next);
                }
                input.value = "";
              });

              wrapper.appendChild(input);
              wrapper.appendChild(listEl);
              td.appendChild(wrapper);
            } else {
              const input = document.createElement("input");
              input.value = row[colIndex] ?? "";
              input.addEventListener("input", (event) => {
                rows[rowIndex][colIndex] = event.target.value;
                scheduleSave();
              });
              td.appendChild(input);
            }
            tr.appendChild(td);
          });
          const actions = document.createElement("td");
          actions.className = "row-actions";
          const viewBtn = document.createElement("button");
          viewBtn.type = "button";
          viewBtn.textContent = "View";
          viewBtn.addEventListener("click", () => {
            const category = rows[rowIndex][categoryIndex] || "";
            const productFolder = rows[rowIndex][productFolderIndex] || "";
            if (!category || !productFolder) return;
            const url = `/product?category=${encodeURIComponent(category)}&folder=${encodeURIComponent(productFolder)}`;
            window.location.href = url;
          });
          actions.appendChild(viewBtn);
          if (viewMode === "live") {
            const draftBtn = document.createElement("button");
            draftBtn.type = "button";
            draftBtn.textContent = "To Draft";
            draftBtn.addEventListener("click", async () => {
              const category = rows[rowIndex][categoryIndex] || "";
              const productFolder = rows[rowIndex][productFolderIndex] || "";
              if (!category || !productFolder) return;
              if (!confirm("Move this item back to Draft?")) return;
              try {
                const response = await fetch("/api/move_to_draft", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    category,
                    folder_name: productFolder,
                  }),
                });
                const payload = await response.json();
                if (!response.ok) {
                  alert(payload.error || "Move failed.");
                  return;
                }
                await autoLoadDefault();
              } catch (error) {
                console.error(error);
                alert("Move failed.");
              }
            });
            actions.appendChild(draftBtn);
          }
          const deleteBtn = document.createElement("button");
          deleteBtn.type = "button";
          deleteBtn.textContent = "Archive";
          deleteBtn.addEventListener("click", async () => {
            const category = rows[rowIndex][categoryIndex] || "";
            const productFolder = rows[rowIndex][productFolderIndex] || "";
            if (!category || !productFolder) return;
            if (!confirm("Move this folder to _Archive?")) return;
            try {
              const response = await fetch("/api/archive", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  category,
                  folder_name: productFolder,
                }),
              });
              const payload = await response.json();
              if (!response.ok) {
                alert(payload.error || "Archive failed.");
                return;
              }
              rows.splice(rowIndex, 1);
              originalNames.splice(rowIndex, 1);
              renderBody();
              updateStatus();
            } catch (error) {
              console.error(error);
              alert("Archive failed.");
            }
          });
          actions.appendChild(deleteBtn);
          tr.appendChild(actions);
          fragment.appendChild(tr);
        });
        tbody.appendChild(fragment);
        emptyState.style.display = rows.length === 0 ? "block" : "none";
      };

      const loadCSVText = (text) => {
        const parsed = parseCSV(text);
        headers = parsed.shift() || [];
        rows = parsed;
        originalNames = rows.map((row) => row[headers.indexOf("product_folder")] || "");
        isDirty = false;
        renderHeader();
        renderBody();
        updateStatus();
        emptyState.style.display = headers.length ? "none" : "block";
        fileHandle = null;
      };

      const renderFolderList = (items) => {
        folderList.innerHTML = "";
        if (!items.length) {
          folderEmpty.style.display = "block";
          return;
        }
        folderEmpty.style.display = "none";
        items.forEach((item) => {
          const row = document.createElement("div");
          row.className = "folder-item";

          const title = document.createElement("div");
          title.className = "folder-title";
          title.textContent = item.product_folder || "(untitled)";

          const meta = document.createElement("div");
          meta.className = "folder-meta";
          meta.textContent = item.category || "Uncategorized";

          row.appendChild(title);
          row.appendChild(meta);
          if (viewMode === "draft") {
            const actions = document.createElement("div");
            actions.className = "row-actions";
            const viewBtn = document.createElement("button");
            viewBtn.type = "button";
            viewBtn.textContent = "View";
            viewBtn.addEventListener("click", () => {
              const category = item.category || "";
              const productFolder = item.product_folder || "";
              if (!category || !productFolder) return;
              const url = `/product?category=${encodeURIComponent(category)}&folder=${encodeURIComponent(productFolder)}&status=draft`;
              window.location.href = url;
            });
            const approveBtn = document.createElement("button");
            approveBtn.type = "button";
            approveBtn.textContent = "Approve";
            approveBtn.addEventListener("click", async () => {
              if (!confirm("Approve this draft and move it live?")) return;
              try {
                const response = await fetch("/api/approve", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    category: item.category,
                    folder_name: item.product_folder,
                  }),
                });
                const payload = await response.json();
                if (!response.ok) {
                  alert(payload.error || "Approve failed.");
                  return;
                }
                await loadFolderList("draft");
                await autoLoadDefault();
              } catch (error) {
                console.error(error);
                alert("Approve failed.");
              }
            });
            actions.appendChild(viewBtn);
            actions.appendChild(approveBtn);
            row.appendChild(actions);
          }
          folderList.appendChild(row);
        });
      };

      const loadFolderList = async (mode) => {
        const endpoint = mode === "archived" ? "/api/archived" : "/api/drafts";
        try {
          const response = await fetch(endpoint, { cache: "no-store" });
          if (!response.ok) return;
          const payload = await response.json();
          renderFolderList(payload.items || []);
        } catch (error) {
          console.error(error);
        }
      };

      const setViewMode = (mode) => {
        viewMode = mode;
        viewTabs.querySelectorAll(".tab-btn").forEach((button) => {
          const isActive = button.dataset.view === mode;
          button.classList.toggle("active", isActive);
        });
        if (mode === "archived" || mode === "draft") {
          tableView.hidden = true;
          folderView.hidden = false;
          folderTitle.textContent = mode === "archived" ? "Archived Products" : "Draft Products";
          statusEl.textContent = mode === "archived"
            ? "Viewing archived products."
            : "Viewing draft products.";
          loadFolderList(mode).catch(console.error);
          return;
        }
        folderView.hidden = true;
        tableView.hidden = false;
        renderBody();
        updateStatus();
      };

      const autoLoadDefault = async () => {
        try {
          const response = await fetch("/api/rows", { cache: "no-store" });
          if (!response.ok) return;
          const data = await response.json();
          if (!data.headers || !data.rows) return;
          headers = data.headers;
          rows = data.rows.map((row) => headers.map((h) => row[h] ?? ""));
          originalNames = rows.map((row) => row[headers.indexOf("product_folder")] || "");
          isDirty = false;
          renderHeader();
          renderBody();
          updateStatus();
          emptyState.style.display = headers.length ? "none" : "block";
          statusEl.textContent = "Auto-loaded products via server.";
          setViewMode(viewMode);
        } catch (error) {
          // Ignore if running on file:// or blocked by CORS.
        }
      };

      const openReadmeEditor = async (rowIndex) => {
        const categoryIndex = headers.indexOf("category");
        const productFolderIndex = headers.indexOf("product_folder");
        const category = rows[rowIndex]?.[categoryIndex] || "";
        const folderName = rows[rowIndex]?.[productFolderIndex] || "";
        if (!category || !folderName) return;
        try {
          const response = await fetch("/api/readme", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              category,
              folder_name: folderName,
              action: "read",
            }),
          });
          const payload = await response.json();
          if (!response.ok) {
            alert(payload.error || "Failed to load README.");
            return;
          }
          readmeRowIndex = rowIndex;
          readmeTitle.textContent = "README.md";
          readmePath.textContent = `${category}/${folderName}/README.md`;
          readmeContent.value = payload.content || "";
          if (readmeDialog.showModal) {
            readmeDialog.showModal();
          } else {
            readmeDialog.setAttribute("open", "true");
          }
        } catch (error) {
          console.error(error);
          alert("Failed to load README.");
        }
      };

      const closeReadmeEditor = () => {
        readmeRowIndex = null;
        if (readmeDialog.close) {
          readmeDialog.close();
        } else {
          readmeDialog.removeAttribute("open");
        }
      };

      const saveReadme = async () => {
        if (readmeRowIndex == null) return;
        const categoryIndex = headers.indexOf("category");
        const productFolderIndex = headers.indexOf("product_folder");
        const category = rows[readmeRowIndex]?.[categoryIndex] || "";
        const folderName = rows[readmeRowIndex]?.[productFolderIndex] || "";
        if (!category || !folderName) return;
        try {
          const response = await fetch("/api/readme", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              category,
              folder_name: folderName,
              action: "write",
              content: readmeContent.value,
            }),
          });
          const payload = await response.json();
          if (!response.ok) {
            alert(payload.error || "Failed to save README.");
            return;
          }
          statusEl.textContent = "README saved.";
          setTimeout(updateStatus, 1500);
          closeReadmeEditor();
        } catch (error) {
          console.error(error);
          alert("Failed to save README.");
        }
      };


      const saveViaApi = async () => {
        if (autosaveTimer) {
          clearTimeout(autosaveTimer);
          autosaveTimer = null;
        }
        saveInFlight = true;
        try {
          const response = await fetch("/api/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              headers,
              rows: rows.map((row) => {
                const out = {};
                headers.forEach((header, index) => {
                  out[header] = row[index] ?? "";
                });
                return out;
              }),
            }),
          });
          const payload = await response.json();
          if (!response.ok) {
            alert(payload.error || "Save failed.");
            return;
          }
          isDirty = false;
          statusEl.textContent = "Saved changes.";
          if (payload.refresh) {
            await autoLoadDefault();
            return;
          }
          setTimeout(updateStatus, 1500);
        } catch (error) {
          console.error(error);
          alert("Save failed.");
        } finally {
          saveInFlight = false;
        }
      };

      closeReadmeBtn.addEventListener("click", closeReadmeEditor);
      saveReadmeBtn.addEventListener("click", () => saveReadme().catch(console.error));
      searchInput.addEventListener("input", () => {
        renderBody();
        updateStatus();
      });
      ukcaFilter.addEventListener("change", (event) => {
        setUkcaFilter(event.target.value);
      });
      autoLoadDefault();

      const autoRefresh = () => {
        if (isDirty || autosaveTimer || saveInFlight) {
          return;
        }
        autoLoadDefault().catch(console.error);
      };

      setInterval(autoRefresh, 30000);
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
          autoRefresh();
        }
      });

      logoutBtn.addEventListener("click", async () => {
        await fetch("/api/logout", { method: "POST" });
        window.location.href = "/login";
      });

      viewTabs.addEventListener("click", (event) => {
        const button = event.target.closest(".tab-btn");
        if (!button) return;
        const mode = button.dataset.view;
        if (!mode) return;
        setViewMode(mode);
      });
})
</script>

<template>
<header>
      <nav class="nav">
        <div class="nav-brand">
          <img src="/logo.png" alt="Geeky Things logo" />
          <strong>GeekyThings</strong>
        </div>
        <div class="nav-center">
          <h1 class="title">GeekyThings Product Manager</h1>
          <p class="subtitle">Manage products, tags, and listing status from one place.</p>
          <p class="version">
          Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
          </p>
        </div>
        <div class="nav-links">
          <RouterLink to="/">Products</RouterLink>
          <RouterLink to="/stock">Stock</RouterLink>
          <RouterLink to="/production">Production</RouterLink>
          <RouterLink to="/events">Events</RouterLink>
          <RouterLink to="/supplies">Supplies</RouterLink>
          <RouterLink to="/add">Add Product</RouterLink>
          <button class="ghost" id="logoutBtn" type="button">Logout</button>
        </div>
      </nav>
      <div class="tabs" id="viewTabs">
        <button class="tab-btn active" type="button" data-view="live">Live</button>
        <button class="tab-btn" type="button" data-view="draft">Draft</button>
        <button class="tab-btn" type="button" data-view="b2b">B2B</button>
        <button class="tab-btn" type="button" data-view="archived">Archived</button>
      </div>
      <div class="panel">
        <div class="controls">
          <input id="searchInput" type="search" placeholder="Search everything..." />
          <select id="ukcaFilter" aria-label="Filter by UKCA status">
            <option value="">UKCA: Any</option>
            <option value="Yes">UKCA: Yes</option>
            <option value="No">UKCA: No</option>
          </select>
        </div>
        <div class="status" id="status">No file loaded.</div>
      </div>
    </header>

    <main>
      <div class="table-wrap" id="tableView">
        <table id="dataTable">
          <colgroup id="colgroup"></colgroup>
          <thead></thead>
          <tbody></tbody>
        </table>
        <div class="empty" id="emptyState">Loading products...</div>
      </div>
      <div class="folder-view" id="folderView" hidden>
        <h2 id="folderTitle">Archived Products</h2>
        <div class="folder-list" id="folderList"></div>
        <div class="empty" id="folderEmpty">No items found.</div>
      </div>
      <div class="footnote">Tip: launch with the provided server to enable rename actions and auto-load.</div>
    </main>

    <dialog id="readmeDialog">
      <div class="dialog-header">
        <div>
          <h2 id="readmeTitle">README.md</h2>
          <p id="readmePath" class="dialog-subtitle"></p>
        </div>
        <button id="closeReadmeBtn" class="ghost" type="button">Close</button>
      </div>
      <div class="dialog-body">
        <textarea id="readmeContent" placeholder="README.md contents..."></textarea>
      </div>
      <div class="dialog-actions">
        <button id="saveReadmeBtn" class="secondary" type="button">Save README</button>
      </div>
    </dialog>
</template>
