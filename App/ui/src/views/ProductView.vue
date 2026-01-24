<script setup>
import { onMounted } from 'vue'
import { APP_VERSION, CHANGELOG_URL } from '../constants'

const version = APP_VERSION
const changeLogUrl = CHANGELOG_URL

onMounted(() => {
const params = new URLSearchParams(window.location.search);
      const categoryParam = params.get("category") || "";
      const folderParam = params.get("folder") || "";
      const statusParam = (params.get("status") || "").toLowerCase();

      const productTitle = document.getElementById("productTitle");
      const categoryInput = document.getElementById("category");
      const skuInput = document.getElementById("sku");
      const ukcaStatus = document.getElementById("ukcaStatus");
      const ukcaAddBtn = document.getElementById("ukcaAddBtn");
      const productFolderInput = document.getElementById("productFolder");
      const tagsInput = document.getElementById("tags");
      const costToMakeInput = document.getElementById("costToMake");
      const salePriceInput = document.getElementById("salePrice");
      const postagePriceInput = document.getElementById("postagePrice");
      const onlinePrice = document.getElementById("onlinePrice");
      const inPersonPrice = document.getElementById("inPersonPrice");
      const colorsInput = document.getElementById("colorsInput");
      const sizesInput = document.getElementById("sizesInput");
      const colorsList = document.getElementById("colorsList");
      const sizesList = document.getElementById("sizesList");
      const colorsSuggestions = document.getElementById("colorsSuggestions");
      const sizesSuggestions = document.getElementById("sizesSuggestions");
      const sizePricingBody = document.getElementById("sizePricingBody");
      const savePricingBtn = document.getElementById("savePricingBtn");
      const listingGroup = document.getElementById("listingGroup");
      const listingLinks = document.getElementById("listingLinks");
      const facebookUrlInput = document.getElementById("facebookUrl");
      const tiktokUrlInput = document.getElementById("tiktokUrl");
      const ebayUrlInput = document.getElementById("ebayUrl");
      const etsyUrlInput = document.getElementById("etsyUrl");
      const saveDetailsBtn = document.getElementById("saveDetailsBtn");
      const renameBtn = document.getElementById("renameBtn");
      const openFolderBtn = document.getElementById("openFolderBtn");
      const statusEl = document.getElementById("status");
      const readmeArea = document.getElementById("readme");
      const saveReadmeBtn = document.getElementById("saveReadmeBtn");
      const mediaGrid = document.getElementById("mediaGrid");
      const threeMfList = document.getElementById("threeMfList");
      const uploadZone = document.getElementById("uploadZone");
      const uploadInput = document.getElementById("uploadInput");
      const logoutBtn = document.getElementById("logoutBtn");
      const ukcaDialog = document.getElementById("ukcaDialog");
      const ukcaForm = document.getElementById("ukcaForm");
      const ukcaProductName = document.getElementById("ukcaProductName");
      const ukcaSku = document.getElementById("ukcaSku");
      const ukcaMaterials = document.getElementById("ukcaMaterials");
      const ukcaIntendedAge = document.getElementById("ukcaIntendedAge");
      const ukcaManufacturer = document.getElementById("ukcaManufacturer");
      const ukcaAddress = document.getElementById("ukcaAddress");
      const ukcaTester = document.getElementById("ukcaTester");
      const ukcaTestDate = document.getElementById("ukcaTestDate");
      const ukcaNotes = document.getElementById("ukcaNotes");
      const ukcaPackSection = document.getElementById("ukcaPackSection");
      const ukcaPackDetails = document.getElementById("ukcaPackDetails");
      const ukcaPackList = document.getElementById("ukcaPackList");
      const printUkcaBtn = document.getElementById("printUkcaBtn");

      const listingOptions = ["Facebook", "TikTok", "Ebay", "Etsy"];
      const baseCategoriesPath = "/Users/dan/GeekyThings/Products/Categories";
      const draftBasePath = "/Users/dan/GeekyThings/Products/Categories/_Draft";

      let headers = [];
      let rows = [];
      let rowIndex = -1;
      let originalCategory = categoryParam;
      let originalFolder = folderParam;
      let currentUkcaStatus = "No";
      let ukcaPackFiles = [];
      let currentColors = [];
      let currentSizes = [];
      let pricingData = { base: {}, sizes: [] };

      const ukcaFileLabels = {
        readme: "UKCA README",
        declaration: "Declaration of Conformity",
        risk_assessment: "Risk Assessment",
        en71: "EN71-1 Compliance Pack",
      };

      const defaultEn71Data = () => ({
        productName: productFolderInput.value || "",
        sku: skuInput.value || "",
        material: "PLA / PETG",
        intendedAge: "3+",
        tester: "Dan Robinson",
        testDate: "",
        dropResult: "PASS",
        tensionResult: "PASS",
        torsionResult: "PASS",
        smallParts: "No",
        warningLabel: "Yes",
        finalResult: "PASS",
        visualNotes: "Visual inspection completed. No sharp edges, burrs, or defects observed. Surface finish smooth.",
        dropNotes: "Drop testing completed. No hazardous breakage observed; any minor separation was blunt with no sharp edges.",
        tensionNotes: "Tension test completed. No hazardous detachment observed; joints remained secure under manual force.",
        torsionNotes: "Torsion test completed. No hazardous fracture observed; no sharp edges created.",
        smallPartsNotes: "Small parts not created. Warning label remains applicable for 3+ age grading.",
        conclusionNotes: "Product either withstood testing or fractured in a non-hazardous manner. No sharp edges or points created.",
      });

      const generateEn71Markdown = (data) => {
        return `# EN71-1 Compliance Pack - ${data.productName} (SKU: ${data.sku})\n\n` +
          `Material: ${data.material}\n` +
          `Intended Age: ${data.intendedAge}\n` +
          `Date Tested: ${data.testDate || "______________________________"}\n` +
          `Tester: ${data.tester}\n\n` +
          `---\n\n` +
          `## 1) EN71-1 Self-Test Checklist (3+ Toys)\n\n` +
          `### A. Visual & Construction Checks\n` +
          `Result: ${data.visualNotes ? "SEE NOTES" : "PASS"}\n\n` +
          `Notes: ${data.visualNotes || "No sharp edges, burrs, or defects observed."}\n\n` +
          `### B. Drop / Impact Test\n` +
          `Method: Drop from 1.0 m onto hard surface - 3 times\n\n` +
          `Result: ${data.dropResult}\n\n` +
          `Notes: ${data.dropNotes || "No hazardous breakage observed."}\n\n` +
          `### C. Tension / Pull Test\n` +
          `Result: ${data.tensionResult}\n\n` +
          `Notes: ${data.tensionNotes || "No hazardous detachment observed."}\n\n` +
          `### D. Torsion / Twist Test\n` +
          `Result: ${data.torsionResult}\n\n` +
          `Notes: ${data.torsionNotes || "No hazardous fracture observed."}\n\n` +
          `### E. Small Parts (Post-Breakage)\n` +
          `Small parts created: ${data.smallParts}\n\n` +
          `Warning label applied: ${data.warningLabel}\n\n` +
          `Notes: ${data.smallPartsNotes || "Not suitable for under 36 months. Small parts."}\n\n` +
          `### F. Overall Mechanical Safety Conclusion\n` +
          `Final Result: ${data.finalResult}\n\n` +
          `Notes: ${data.conclusionNotes || "Product either withstood testing or fractured in a non-hazardous manner."}\n\n` +
          `Signature: ${data.tester}\n` +
          `Date: ${data.testDate || "______________________________"}\n\n` +
          `---\n\n` +
          `## 2) Packaging Warning Labels & Age Grading (UKCA / EN71-1)\n\n` +
          `**Mandatory Age Warning (Plain):**\n` +
          `Not suitable for children under 36 months. Small parts.\n\n` +
          `**Recommended Notes:**\n` +
          `- Sensory fidget toy.\n` +
          `- Not a teething toy.\n` +
          `- Adult supervision recommended.\n` +
          `- Inspect regularly and discard if damaged.\n\n` +
          `**Manufacturer / Responsible Person:**\n` +
          `GeekyThingsUK\n` +
          `United Kingdom\n` +
          `www.geekythings.co.uk\n\n` +
          `---\n\n` +
          `## 3) EN71-1 Compliance Section for UKCA Technical File\n\n` +
          `Product Name: ${data.productName}\n` +
          `SKU(s): ${data.sku}\n` +
          `Material: ${data.material}\n` +
          `Intended Age Group: ${data.intendedAge}\n\n` +
          `The product is a 3D-printed articulated sensory fidget toy manufactured from PLA or PETG. ` +
          `It contains no electronics, no magnets, and no metal components.\n\n` +
          `Applicable Standard: EN 71-1:2014 + A1:2018\n\n` +
          `Based on the testing above, the product is considered to comply with the mechanical and physical ` +
          `safety requirements of EN 71-1 for toys intended for children aged 3 years and over.\n`;
      };

      const updateUkcaDisplay = () => {
        const statusValue = currentUkcaStatus || "No";
        ukcaStatus.textContent = statusValue;
        ukcaStatus.className = "ukca-badge";
        if (statusValue === "Yes") {
          ukcaStatus.classList.add("is-yes");
        } else if (statusValue === "N/A") {
          ukcaStatus.classList.add("is-na");
        } else {
          ukcaStatus.classList.add("is-no");
        }
        if (statusValue === "Yes") {
          ukcaAddBtn.textContent = "View/Edit UKCA Pack";
          ukcaPackSection.hidden = false;
        } else {
          ukcaAddBtn.textContent = "Add UKCA Pack";
          ukcaPackSection.hidden = true;
        }
      };

      const openUkcaSection = async (openEn71 = false) => {
        ukcaPackDetails.open = true;
        await loadUkcaPackList();
        if (openEn71) {
          const en71Detail = ukcaPackList.querySelector('details[data-file-key="en71"]');
          if (en71Detail) {
            en71Detail.open = true;
          }
        }
        ukcaPackSection.scrollIntoView({ behavior: "smooth", block: "start" });
      };

      const loadData = async () => {
        const response = await fetch("/api/rows", { cache: "no-store" });
        if (!response.ok) return;
        const data = await response.json();
        headers = data.headers || [];
        rows = data.rows || [];
        rowIndex = rows.findIndex(
          (row) => row.category === categoryParam && row.product_folder === folderParam
        );
        if (rowIndex === -1) {
          statusEl.textContent = "Product not found.";
          return;
        }
        const row = rows[rowIndex];
        productTitle.textContent = row.product_folder || "Product Details";
        categoryInput.value = row.category || "";
        skuInput.value = row.sku || "";
        currentUkcaStatus = row.UKCA || "No";
        updateUkcaDisplay();
        productFolderInput.value = row.product_folder || "";
        tagsInput.value = row.tags || "";
        costToMakeInput.value = row["Cost To Make"] || "";
        salePriceInput.value = row["Sale Price"] || "";
        postagePriceInput.value = row["Postage Price"] || "";
        updateBasePricingSummary();
        currentColors = parseList(row.Colors || "");
        currentSizes = parseList(row.Sizes || "");
        renderChips(currentColors, colorsList, removeColor);
        renderChips(currentSizes, sizesList, removeSize);
        facebookUrlInput.value = row["Facebook URL"] || "";
        tiktokUrlInput.value = row["TikTok URL"] || "";
        ebayUrlInput.value = row["Ebay URL"] || "";
        etsyUrlInput.value = row["Etsy URL"] || "";

        listingGroup.innerHTML = "";
        const updateListingLinks = () => {
          listingLinks.innerHTML = "";
          const urlMap = {
            Facebook: facebookUrlInput.value.trim(),
            TikTok: tiktokUrlInput.value.trim(),
            Ebay: ebayUrlInput.value.trim(),
            Etsy: etsyUrlInput.value.trim(),
          };
          listingGroup.querySelectorAll("input[type=checkbox]").forEach((checkbox) => {
            const platform = checkbox.dataset.platform;
            checkbox.checked = Boolean(urlMap[platform]);
          });
          Object.entries(urlMap).forEach(([platform, url]) => {
            if (!url) return;
            const link = document.createElement("a");
            link.href = url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = platform;
            listingLinks.appendChild(link);
          });
        };
        listingOptions.forEach((option) => {
          const label = document.createElement("label");
          label.className = "listing-option";
          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.disabled = true;
          checkbox.dataset.platform = option;
          const text = document.createElement("span");
          text.textContent = option;
          label.appendChild(checkbox);
          label.appendChild(text);
          listingGroup.appendChild(label);
        });
        updateListingLinks();
        [facebookUrlInput, tiktokUrlInput, ebayUrlInput, etsyUrlInput].forEach((input) => {
          input.addEventListener("input", updateListingLinks);
        });

        populateSuggestions();

        await loadPricing();
        await loadReadme();
        await loadMedia();
        await load3mf();
        await loadUkcaPackList();
      };

      const parseList = (value) => {
        return (value || "")
          .split(",")
          .map((item) => item.trim())
          .filter((item) => item);
      };

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

      const renderChips = (items, container, onRemove) => {
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

      const addToList = (value, list, setter, container, removeFn) => {
        const cleaned = (value || "").trim();
        if (!cleaned) return;
        const lower = cleaned.toLowerCase();
        if (list.some((item) => item.toLowerCase() === lower)) return;
        const next = [...list, cleaned];
        setter(next);
        renderChips(next, container, removeFn);
      };

      const removeColor = (value) => {
        currentColors = currentColors.filter((item) => item !== value);
        renderChips(currentColors, colorsList, removeColor);
      };

      const removeSize = (value) => {
        currentSizes = currentSizes.filter((item) => item !== value);
        renderChips(currentSizes, sizesList, removeSize);
        renderSizePricing();
      };

      const populateSuggestions = () => {
        const colorValues = [];
        const sizeValues = [];
        rows.forEach((row) => {
          colorValues.push(...parseList(row.Colors || ""));
          sizeValues.push(...parseList(row.Sizes || ""));
        });
        colorsSuggestions.innerHTML = "";
        sizesSuggestions.innerHTML = "";
        uniqueSorted(colorValues).forEach((value) => {
          const option = document.createElement("option");
          option.value = value;
          colorsSuggestions.appendChild(option);
        });
        uniqueSorted(sizeValues).forEach((value) => {
          const option = document.createElement("option");
          option.value = value;
          sizesSuggestions.appendChild(option);
        });
      };

      const parsePrice = (value) => {
        const number = parseFloat(value);
        return Number.isFinite(number) ? number : 0;
      };

      const formatPrice = (value) => {
        if (!Number.isFinite(value)) return "0.00";
        return value.toFixed(2);
      };

      const updateBasePricingSummary = () => {
        const sale = parsePrice(salePriceInput.value);
        const postage = parsePrice(postagePriceInput.value);
        inPersonPrice.textContent = `In-person price: ${formatPrice(sale)} GBP`;
        onlinePrice.textContent = `Online price: ${formatPrice(sale + postage)} GBP`;
      };

      const renderSizePricing = () => {
        sizePricingBody.innerHTML = "";
        if (!currentSizes.length) {
          const emptyRow = document.createElement("tr");
          const cell = document.createElement("td");
          cell.colSpan = 5;
          cell.textContent = "Add sizes to enable size-based pricing.";
          emptyRow.appendChild(cell);
          sizePricingBody.appendChild(emptyRow);
          return;
        }
        const sizeMap = new Map();
        (pricingData.sizes || []).forEach((entry) => {
          if (!entry || !entry.size) return;
          sizeMap.set(entry.size, entry);
        });
        const makeInput = (value, field) => {
          const input = document.createElement("input");
          input.type = "number";
          input.min = "0";
          input.step = "0.01";
          input.value = value || "";
          input.dataset.field = field;
          input.className = "price-input";
          return input;
        };
        const updateRowSummary = (summary, saleInput, postageInput) => {
          const sale = parsePrice(saleInput.value);
          const postage = parsePrice(postageInput.value);
          summary.textContent = `Online: ${formatPrice(sale + postage)} GBP · In-person: ${formatPrice(sale)} GBP`;
        };

        currentSizes
          .slice()
          .sort((a, b) => a.localeCompare(b))
          .forEach((size) => {
            const entry = sizeMap.get(size) || {};
            const row = document.createElement("tr");
            row.dataset.size = size;

            const sizeCell = document.createElement("td");
            sizeCell.textContent = size;
            row.appendChild(sizeCell);

            const costCell = document.createElement("td");
            const costInput = makeInput(entry.cost_to_make, "cost_to_make");
            costCell.appendChild(costInput);
            row.appendChild(costCell);

            const saleCell = document.createElement("td");
            const saleInput = makeInput(entry.sale_price, "sale_price");
            saleCell.appendChild(saleInput);
            row.appendChild(saleCell);

            const postageCell = document.createElement("td");
            const postageInput = makeInput(entry.postage_price, "postage_price");
            postageCell.appendChild(postageInput);
            row.appendChild(postageCell);

            const summaryCell = document.createElement("td");
            const summary = document.createElement("div");
            summary.className = "price-summary";
            updateRowSummary(summary, saleInput, postageInput);
            summaryCell.appendChild(summary);
            row.appendChild(summaryCell);

            [saleInput, postageInput].forEach((input) => {
              input.addEventListener("input", () => updateRowSummary(summary, saleInput, postageInput));
            });

            sizePricingBody.appendChild(row);
          });
      };

      const loadPricing = async () => {
        const response = await fetch("/api/pricing", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: categoryParam,
            folder_name: productFolderInput.value,
            status: statusParam,
            action: "read",
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Failed to load pricing.";
          return;
        }
        pricingData = payload.pricing || { base: {}, sizes: [] };
        renderSizePricing();
      };

      const collectSizePricing = () => {
        const entries = [];
        sizePricingBody.querySelectorAll("tr[data-size]").forEach((row) => {
          const size = row.dataset.size || "";
          const cost = row.querySelector('[data-field="cost_to_make"]')?.value.trim() || "";
          const sale = row.querySelector('[data-field="sale_price"]')?.value.trim() || "";
          const postage = row.querySelector('[data-field="postage_price"]')?.value.trim() || "";
          if (!cost && !sale && !postage) return;
          entries.push({
            size,
            cost_to_make: cost,
            sale_price: sale,
            postage_price: postage,
          });
        });
        return entries;
      };

      const savePricing = async () => {
        await saveDetails();
        const pricingPayload = {
          base: {
            cost_to_make: costToMakeInput.value.trim(),
            sale_price: salePriceInput.value.trim(),
            postage_price: postagePriceInput.value.trim(),
          },
          sizes: collectSizePricing(),
        };
        const response = await fetch("/api/pricing", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: categoryParam,
            folder_name: productFolderInput.value,
            status: statusParam,
            action: "write",
            pricing: pricingPayload,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Failed to save pricing.";
          return;
        }
        pricingData = pricingPayload;
        renderSizePricing();
        statusEl.textContent = "Pricing saved.";
      };

      const loadReadme = async () => {
        const response = await fetch("/api/readme", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: categoryParam,
            folder_name: productFolderInput.value,
            status: statusParam,
            action: "read",
          }),
        });
        const payload = await response.json();
        if (!response.ok) return;
        readmeArea.value = payload.content || "";
      };

      const loadMedia = async () => {
        const response = await fetch(
          `/api/media?category=${encodeURIComponent(categoryParam)}&folder=${encodeURIComponent(productFolderInput.value)}&status=${encodeURIComponent(statusParam)}`
        );
        if (!response.ok) return;
        const payload = await response.json();
        const files = payload.files || [];
        mediaGrid.innerHTML = "";
        files.forEach((file) => {
          const ext = file.name.split(".").pop().toLowerCase();
          const wrapper = document.createElement("div");
          wrapper.className = "media-item";
          if (["mp4", "mov", "webm", "m4v"].includes(ext)) {
            const video = document.createElement("video");
            video.src = file.url;
            video.controls = true;
            wrapper.appendChild(video);
          } else {
            const img = document.createElement("img");
            img.src = file.url;
            img.alt = file.name;
            wrapper.appendChild(img);
          }
          const actions = document.createElement("div");
          actions.className = "media-actions";
          const removeBtn = document.createElement("button");
          removeBtn.className = "btn ghost";
          removeBtn.type = "button";
          removeBtn.textContent = "X";
          removeBtn.title = "Remove";
          removeBtn.addEventListener("click", () => {
            if (!confirm("Move this file to _Deleted?")) return;
            deleteFile(file.rel_path).catch(console.error);
          });
          actions.appendChild(removeBtn);
          wrapper.appendChild(actions);
          mediaGrid.appendChild(wrapper);
        });
      };

      const load3mf = async () => {
        const response = await fetch(
          `/api/3mf?category=${encodeURIComponent(categoryParam)}&folder=${encodeURIComponent(productFolderInput.value)}&status=${encodeURIComponent(statusParam)}`
        );
        if (!response.ok) return;
        const payload = await response.json();
        const files = payload.files || [];
        threeMfList.innerHTML = "";
        if (!files.length) {
          threeMfList.textContent = "No .3mf files found.";
          return;
        }
        files.forEach((file) => {
          const row = document.createElement("div");
          row.className = "file-item";

          const info = document.createElement("div");
          const name = document.createElement("div");
          name.className = "file-name";
          name.textContent = file.name;
          const path = document.createElement("div");
          path.className = "file-path";
          path.textContent = file.rel_path || "";
          info.appendChild(name);
          info.appendChild(path);

          const actions = document.createElement("div");
          actions.className = "file-actions";
          const openLink = document.createElement("button");
          openLink.className = "btn ghost";
          openLink.type = "button";
          openLink.textContent = "Open";
          openLink.addEventListener("click", async () => {
            try {
              const response = await fetch("/api/file_token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  category: categoryParam,
                  folder_name: productFolderInput.value,
                  status: statusParam,
                  rel_path: file.rel_path,
                }),
              });
              const payload = await response.json();
              if (!response.ok) {
                statusEl.textContent = payload.error || "Failed to open file.";
                return;
              }
              const tokenUrl = `${window.location.origin}/files-token/${payload.token}/${encodeURIComponent(file.name)}`;
              const targetUrl = `bambustudioopen://${encodeURIComponent(tokenUrl)}`;
              window.open(targetUrl, "_blank");
            } catch (error) {
              console.error(error);
              statusEl.textContent = "Failed to open file.";
            }
          });

          const downloadLink = document.createElement("a");
          downloadLink.className = "btn ghost";
          downloadLink.textContent = "Download";
          downloadLink.href = file.url || "#";
          downloadLink.target = "_blank";
          downloadLink.rel = "noopener noreferrer";

          const copyBtn = document.createElement("button");
          copyBtn.className = "btn ghost";
          copyBtn.type = "button";
          copyBtn.textContent = "Copy Path";
          copyBtn.addEventListener("click", () => {
            const text = file.abs_path || file.url || "";
            if (!text) return;
            navigator.clipboard?.writeText(text).catch(() => {});
          });
          const removeBtn = document.createElement("button");
          removeBtn.className = "btn ghost";
          removeBtn.type = "button";
          removeBtn.textContent = "Remove";
          removeBtn.addEventListener("click", () => {
            if (!confirm("Move this file to _Deleted?")) return;
            deleteFile(file.rel_path).catch(console.error);
          });

          actions.appendChild(openLink);
          actions.appendChild(downloadLink);
          actions.appendChild(copyBtn);
          actions.appendChild(removeBtn);

          row.appendChild(info);
          row.appendChild(actions);
          threeMfList.appendChild(row);
        });
      };

      const loadUkcaPackList = async () => {
        if (currentUkcaStatus !== "Yes") {
          ukcaPackList.innerHTML = '<div class="ukca-pack-empty">No UKCA pack yet.</div>';
          return;
        }
        const response = await fetch(
          `/api/ukca_pack?category=${encodeURIComponent(categoryParam)}&folder=${encodeURIComponent(productFolderInput.value)}&status=${encodeURIComponent(statusParam)}`
        );
        if (!response.ok) return;
        const payload = await response.json();
        const files = payload.files || [];
        ukcaPackFiles = files.filter((file) => file.exists);
        ukcaPackList.innerHTML = "";
        if (!ukcaPackFiles.length) {
          ukcaPackList.innerHTML = '<div class="ukca-pack-empty">UKCA files not found.</div>';
          return;
        }
        ukcaPackFiles.forEach((file) => {
          const details = document.createElement("details");
          details.className = "ukca-pack-file";
          details.dataset.fileKey = file.key;
          const summary = document.createElement("summary");
          summary.textContent = ukcaFileLabels[file.key] || file.key;
          const textarea = document.createElement("textarea");
          textarea.placeholder = "Loading...";
          const actions = document.createElement("div");
          actions.className = "actions";
          actions.style.marginTop = "10px";
          const saveBtn = document.createElement("button");
          saveBtn.className = "btn secondary";
          saveBtn.type = "button";
          saveBtn.textContent = "Save UKCA File";
          saveBtn.addEventListener("click", () => {
            saveUkcaFile(file.key, textarea.value).catch(console.error);
          });
          actions.appendChild(saveBtn);

          if (file.key === "en71") {
            const form = document.createElement("div");
            form.className = "ukca-en71-form";
            const grid = document.createElement("div");
            grid.className = "ukca-en71-grid";
            const data = defaultEn71Data();
            const productInput = document.createElement("input");
            productInput.value = data.productName;
            const skuField = document.createElement("input");
            skuField.value = data.sku;
            const materialField = document.createElement("input");
            materialField.value = data.material;
            const ageField = document.createElement("input");
            ageField.value = data.intendedAge;
            const testerField = document.createElement("input");
            testerField.value = data.tester;
            const dateField = document.createElement("input");
            dateField.type = "date";
            const dropResult = document.createElement("select");
            ["PASS", "FAIL"].forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value;
              dropResult.appendChild(option);
            });
            const tensionResult = document.createElement("select");
            ["PASS", "FAIL"].forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value;
              tensionResult.appendChild(option);
            });
            const torsionResult = document.createElement("select");
            ["PASS", "FAIL"].forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value;
              torsionResult.appendChild(option);
            });
            const smallParts = document.createElement("select");
            ["No", "Yes"].forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value;
              smallParts.appendChild(option);
            });
            const warningLabel = document.createElement("select");
            ["Yes", "No"].forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value;
              warningLabel.appendChild(option);
            });
            const finalResult = document.createElement("select");
            ["PASS", "FAIL"].forEach((value) => {
              const option = document.createElement("option");
              option.value = value;
              option.textContent = value;
              finalResult.appendChild(option);
            });

            const field = (label, input) => {
              const wrapper = document.createElement("div");
              const title = document.createElement("label");
              title.textContent = label;
              wrapper.appendChild(title);
              wrapper.appendChild(input);
              return wrapper;
            };

            grid.appendChild(field("Product name", productInput));
            grid.appendChild(field("SKU", skuField));
            grid.appendChild(field("Material", materialField));
            grid.appendChild(field("Intended age", ageField));
            grid.appendChild(field("Tester", testerField));
            grid.appendChild(field("Test date", dateField));
            grid.appendChild(field("Drop test", dropResult));
            grid.appendChild(field("Tension test", tensionResult));
            grid.appendChild(field("Torsion test", torsionResult));
            grid.appendChild(field("Small parts created", smallParts));
            grid.appendChild(field("Warning label applied", warningLabel));
            grid.appendChild(field("Final result", finalResult));
            form.appendChild(grid);

            const notesLabel = (labelText) => {
              const wrapper = document.createElement("div");
              const label = document.createElement("label");
              label.textContent = labelText;
              const area = document.createElement("textarea");
              area.rows = 2;
              wrapper.appendChild(label);
              wrapper.appendChild(area);
              return { wrapper, area };
            };

            const visualNotes = notesLabel("Visual checks notes");
            const dropNotes = notesLabel("Drop test notes");
            const tensionNotes = notesLabel("Tension test notes");
            const torsionNotes = notesLabel("Torsion test notes");
            const smallPartsNotes = notesLabel("Small parts notes");
            const conclusionNotes = notesLabel("Conclusion notes");
            visualNotes.area.value = data.visualNotes;
            dropNotes.area.value = data.dropNotes;
            tensionNotes.area.value = data.tensionNotes;
            torsionNotes.area.value = data.torsionNotes;
            smallPartsNotes.area.value = data.smallPartsNotes;
            conclusionNotes.area.value = data.conclusionNotes;
            form.appendChild(visualNotes.wrapper);
            form.appendChild(dropNotes.wrapper);
            form.appendChild(tensionNotes.wrapper);
            form.appendChild(torsionNotes.wrapper);
            form.appendChild(smallPartsNotes.wrapper);
            form.appendChild(conclusionNotes.wrapper);

            const generateBtn = document.createElement("button");
            generateBtn.className = "btn ghost";
            generateBtn.type = "button";
            generateBtn.textContent = "Generate EN71-1 Content";
            generateBtn.addEventListener("click", () => {
              const payload = {
                productName: productInput.value.trim(),
                sku: skuField.value.trim(),
                material: materialField.value.trim(),
                intendedAge: ageField.value.trim(),
                tester: testerField.value.trim(),
                testDate: dateField.value,
                dropResult: dropResult.value,
                tensionResult: tensionResult.value,
                torsionResult: torsionResult.value,
                smallParts: smallParts.value,
                warningLabel: warningLabel.value,
                finalResult: finalResult.value,
                visualNotes: visualNotes.area.value.trim(),
                dropNotes: dropNotes.area.value.trim(),
                tensionNotes: tensionNotes.area.value.trim(),
                torsionNotes: torsionNotes.area.value.trim(),
                smallPartsNotes: smallPartsNotes.area.value.trim(),
                conclusionNotes: conclusionNotes.area.value.trim(),
              };
              textarea.value = generateEn71Markdown(payload);
            });
            form.appendChild(generateBtn);
            details.appendChild(summary);
            details.appendChild(form);
            details.appendChild(textarea);
            details.appendChild(actions);
          } else {
            details.appendChild(summary);
            details.appendChild(textarea);
            details.appendChild(actions);
          }
          details.appendChild(summary);
          details.appendChild(textarea);
          details.appendChild(actions);
          details.addEventListener("toggle", () => {
            if (!details.open || details.dataset.loaded === "true") return;
            loadUkcaFile(file.key, textarea)
              .then(() => {
                details.dataset.loaded = "true";
              })
              .catch(console.error);
          });
          ukcaPackList.appendChild(details);
        });
      };

      const loadUkcaFile = async (fileKey, textarea) => {
        const response = await fetch("/api/ukca_pack", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: categoryParam,
            folder_name: productFolderInput.value,
            status: statusParam,
            action: "read",
            file: fileKey,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Failed to load UKCA file.";
          return;
        }
        textarea.value = payload.content || "";
      };

      const saveDetails = async () => {
        const selectedListings = listingOptions.filter((platform) => {
          if (platform === "Facebook") return facebookUrlInput.value.trim();
          if (platform === "TikTok") return tiktokUrlInput.value.trim();
          if (platform === "Ebay") return ebayUrlInput.value.trim();
          if (platform === "Etsy") return etsyUrlInput.value.trim();
          return false;
        });

        const row = {
          category: categoryInput.value,
          product_folder: productFolderInput.value.trim(),
          sku: skuInput.value.trim(),
          UKCA: currentUkcaStatus,
          Listings: selectedListings.join(", "),
          tags: tagsInput.value.trim(),
          Colors: currentColors.join(", "),
          Sizes: currentSizes.join(", "),
          "Cost To Make": costToMakeInput.value.trim(),
          "Sale Price": salePriceInput.value.trim(),
          "Postage Price": postagePriceInput.value.trim(),
          "Facebook URL": facebookUrlInput.value.trim(),
          "TikTok URL": tiktokUrlInput.value.trim(),
          "Ebay URL": ebayUrlInput.value.trim(),
          "Etsy URL": etsyUrlInput.value.trim(),
        };

        const response = await fetch("/api/update_row", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            old_category: originalCategory,
            old_product_folder: originalFolder,
            row,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Save failed.";
          return;
        }
        const updatedRow = payload.row || row;
        statusEl.textContent = "Details saved.";
        originalCategory = updatedRow.category;
        originalFolder = updatedRow.product_folder;
        categoryInput.value = updatedRow.category || categoryInput.value;
        productFolderInput.value = updatedRow.product_folder || productFolderInput.value;
        const statusQuery = statusParam ? `&status=${encodeURIComponent(statusParam)}` : "";
        history.replaceState(
          {},
          "",
          `/product?category=${encodeURIComponent(updatedRow.category)}&folder=${encodeURIComponent(updatedRow.product_folder)}${statusQuery}`
        );
      };

      const renameFolder = async () => {
        const newName = productFolderInput.value.trim();
        if (!newName || newName === originalFolder) return;
        const response = await fetch("/api/rename", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: originalCategory,
            old_name: originalFolder,
            new_name: newName,
            status: statusParam,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Rename failed.";
          return;
        }
        statusEl.textContent = "Folder renamed.";
        originalFolder = newName;
        await saveDetails();
        await loadMedia();
        await load3mf();
      };

      const openFolder = () => {
        const basePath = statusParam === "draft" ? draftBasePath : baseCategoriesPath;
        const rawPath = `${basePath}/${categoryParam}/${productFolderInput.value}`;
        const url = encodeURI(`file://${rawPath}`);
        const popup = window.open(url, "_blank");
        if (!popup) {
          navigator.clipboard?.writeText(rawPath).catch(() => {});
          alert("Popup blocked. Path copied to clipboard.");
        }
      };

      const saveReadme = async () => {
        const response = await fetch("/api/readme", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: categoryParam,
            folder_name: productFolderInput.value,
            status: statusParam,
            action: "write",
            content: readmeArea.value,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Save README failed.";
          return;
        }
        statusEl.textContent = "README saved.";
      };

      const openUkcaDialog = () => {
        ukcaProductName.value = productFolderInput.value || "";
        ukcaSku.value = skuInput.value || "";
        if (!ukcaIntendedAge.value) ukcaIntendedAge.value = "3+";
        if (!ukcaManufacturer.value) ukcaManufacturer.value = "GeekyThingsUK";
        if (!ukcaAddress.value) ukcaAddress.value = "United Kingdom";
        if (!ukcaTester.value) ukcaTester.value = "Dan Robinson";
        if (!ukcaTestDate.value) {
          const today = new Date();
          const yyyy = today.getFullYear();
          const mm = String(today.getMonth() + 1).padStart(2, "0");
          const dd = String(today.getDate()).padStart(2, "0");
          ukcaTestDate.value = `${yyyy}-${mm}-${dd}`;
        }
        ukcaDialog.showModal();
      };

      const submitUkcaPack = async (event) => {
        event.preventDefault();
        const payload = {
          category: categoryParam,
          folder_name: productFolderInput.value,
          status: statusParam,
          product_name: ukcaProductName.value.trim(),
          sku: ukcaSku.value.trim(),
          materials: ukcaMaterials.value.trim(),
          intended_age: ukcaIntendedAge.value.trim(),
          manufacturer: ukcaManufacturer.value.trim(),
          address: ukcaAddress.value.trim(),
          tester: ukcaTester.value.trim(),
          test_date: ukcaTestDate.value.trim(),
          notes: ukcaNotes.value.trim(),
        };
        const response = await fetch("/api/ukca_create", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok) {
          statusEl.textContent = result.error || "UKCA pack creation failed.";
          return;
        }
        statusEl.textContent = "UKCA pack created.";
        currentUkcaStatus = "Yes";
        if (rows[rowIndex]) {
          rows[rowIndex].UKCA = "Yes";
        }
        updateUkcaDisplay();
        await openUkcaSection(true);
        ukcaDialog.close();
      };

      const saveUkcaFile = async (fileKey, content) => {
        const response = await fetch("/api/ukca_pack", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: categoryParam,
            folder_name: productFolderInput.value,
            status: statusParam,
            action: "write",
            file: fileKey,
            content,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Failed to save UKCA file.";
          return;
        }
        statusEl.textContent = "UKCA file saved.";
      };

      saveDetailsBtn.addEventListener("click", () => saveDetails().catch(console.error));
      savePricingBtn.addEventListener("click", () => savePricing().catch(console.error));
      renameBtn.addEventListener("click", () => renameFolder().catch(console.error));
      openFolderBtn.addEventListener("click", openFolder);
      saveReadmeBtn.addEventListener("click", () => saveReadme().catch(console.error));
      [costToMakeInput, salePriceInput, postagePriceInput].forEach((input) => {
        input.addEventListener("input", updateBasePricingSummary);
      });
      colorsInput.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        addToList(colorsInput.value, currentColors, (list) => {
          currentColors = list;
        }, colorsList, removeColor);
        colorsInput.value = "";
      });
      sizesInput.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        addToList(sizesInput.value, currentSizes, (list) => {
          currentSizes = list;
        }, sizesList, removeSize);
        renderSizePricing();
        sizesInput.value = "";
      });
      ukcaAddBtn.addEventListener("click", () => {
        if (currentUkcaStatus === "Yes") {
          openUkcaSection().catch(console.error);
          return;
        }
        openUkcaDialog();
      });
      ukcaForm.addEventListener("submit", submitUkcaPack);
      ukcaPackDetails.addEventListener("toggle", () => {
        if (ukcaPackDetails.open) {
          loadUkcaPackList().catch(console.error);
        }
      });
      printUkcaBtn.addEventListener("click", () => {
        printUkcaPack().catch(console.error);
      });

      logoutBtn.addEventListener("click", async () => {
        await fetch("/api/logout", { method: "POST" });
        window.location.href = "/login";
      });

      const printUkcaPack = async () => {
        const response = await fetch(
          `/api/ukca_pack?category=${encodeURIComponent(categoryParam)}&folder=${encodeURIComponent(productFolderInput.value)}&status=${encodeURIComponent(statusParam)}`
        );
        if (!response.ok) return;
        const payload = await response.json();
        const files = (payload.files || [])
          .filter((file) => file.exists)
          .filter((file) => file.key !== "readme");
        if (!files.length) {
          statusEl.textContent = "No UKCA files to print.";
          return;
        }
        const sections = [];
        for (const file of files) {
          const fileResponse = await fetch("/api/ukca_pack", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              category: categoryParam,
              folder_name: productFolderInput.value,
              status: statusParam,
              action: "read",
              file: file.key,
            }),
          });
          const filePayload = await fileResponse.json();
          if (!fileResponse.ok) continue;
          sections.push({
            title: ukcaFileLabels[file.key] || file.key,
            content: filePayload.content || "",
          });
        }
        const printWindow = window.open("", "_blank");
        if (!printWindow) {
          alert("Popup blocked. Allow popups to print.");
          return;
        }
        const styles = `
          body { font-family: Arial, sans-serif; padding: 24px; color: #0f172a; }
          h1 { font-size: 20px; margin-bottom: 6px; }
          h2 { margin-top: 24px; font-size: 16px; }
          pre { white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; background: #f8fafc; padding: 12px; border-radius: 8px; }
        `;
        const html = `
          <html>
            <head><title>UKCA Pack</title><style>${styles}</style></head>
            <body>
              <h1>UKCA Pack - ${productFolderInput.value}</h1>
              ${sections.map((section) => '<h2>' + section.title + '</h2><pre>' + section.content + '</pre>').join('')}
            </body>
          </html>
        `;
        printWindow.document.open();
        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
      };

      const deleteFile = async (relPath) => {
        const response = await fetch("/api/delete_file", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            category: categoryParam,
            folder_name: productFolderInput.value,
            status: statusParam,
            rel_path: relPath,
          }),
        });
        const payload = await response.json();
        if (!response.ok) {
          statusEl.textContent = payload.error || "Delete failed.";
          return;
        }
        statusEl.textContent = "File moved to _Deleted.";
        await loadMedia();
        await load3mf();
      };

      const uploadFiles = async (files) => {
        if (!files || !files.length) return;
        const formData = new FormData();
        formData.append("category", categoryParam);
        formData.append("folder_name", productFolderInput.value);
        formData.append("status", statusParam);
        formData.append("sku", skuInput.value.trim());
        Array.from(files).forEach((file) => formData.append("files", file));
        statusEl.textContent = "Uploading files...";
        try {
          const response = await fetch("/api/upload", {
            method: "POST",
            body: formData,
          });
          const payload = await response.json();
          if (!response.ok) {
            statusEl.textContent = payload.error || "Upload failed.";
            return;
          }
          statusEl.textContent = `Uploaded ${payload.saved?.length || 0} file(s).`;
          await loadMedia();
          await load3mf();
        } catch (error) {
          console.error(error);
          statusEl.textContent = "Upload failed.";
        }
      };

      uploadZone.addEventListener("click", () => uploadInput.click());
      uploadInput.addEventListener("change", (event) => {
        uploadFiles(event.target.files).catch(console.error);
        uploadInput.value = "";
      });
      uploadZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadZone.classList.add("dragover");
      });
      uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("dragover");
      });
      uploadZone.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadZone.classList.remove("dragover");
        uploadFiles(event.dataTransfer.files).catch(console.error);
      });

      if (!categoryParam || !folderParam) {
        statusEl.textContent = "Missing product details in URL.";
      } else {
        loadData().catch(console.error);
      }
})
</script>

<template>
<header>
      <nav class="nav">
        <div class="nav-brand">
          <strong>GeekyThings</strong>
        </div>
        <div class="nav-links">
          <RouterLink to="/">Products</RouterLink>
          <RouterLink to="/stock">Stock</RouterLink>
          <RouterLink to="/add">Add Product</RouterLink>
          <button class="ghost" id="logoutBtn" type="button">Logout</button>
        </div>
      </nav>
      <h1 id="productTitle">Product Details</h1>
      <div class="version">
        Version <a :href="changeLogUrl" target="_blank" rel="noopener noreferrer">{{ version }}</a>
      </div>
    </header>

    <main>
      <section class="card">
        <div class="grid">
          <div>
            <label for="category">Category</label>
            <input id="category" type="text" disabled />
          </div>
          <div>
            <label for="sku">SKU</label>
            <input id="sku" type="text" />
          </div>
          <div>
            <label>UKCA status</label>
            <div class="ukca-status">
              <span class="ukca-badge is-no" id="ukcaStatus">No</span>
              <button class="btn ghost" id="ukcaAddBtn" type="button">Add UKCA Pack</button>
            </div>
          </div>
        </div>
        <div class="grid" style="margin-top: 12px;">
          <div>
            <label for="productFolder">Product folder</label>
            <input id="productFolder" type="text" />
          </div>
          <div>
            <label for="tags">Tags</label>
            <input id="tags" type="text" placeholder="comma,separated,tags" />
          </div>
        </div>
        <div class="grid" style="margin-top: 12px;">
          <div>
            <label for="colorsInput">Colours</label>
            <input id="colorsInput" type="text" list="colorsSuggestions" placeholder="Add colour and press Enter" />
            <datalist id="colorsSuggestions"></datalist>
            <div class="variant-list" id="colorsList"></div>
          </div>
          <div>
            <label for="sizesInput">Sizes</label>
            <input id="sizesInput" type="text" list="sizesSuggestions" placeholder="Add size and press Enter" />
            <datalist id="sizesSuggestions"></datalist>
            <div class="variant-list" id="sizesList"></div>
          </div>
        </div>
        <div class="grid" style="margin-top: 12px;">
          <div>
            <label for="costToMake">Cost to make</label>
            <input id="costToMake" type="number" min="0" step="0.01" placeholder="0.00" />
          </div>
          <div>
            <label for="salePrice">Sale price</label>
            <input id="salePrice" type="number" min="0" step="0.01" placeholder="0.00" />
          </div>
          <div>
            <label for="postagePrice">Postage price</label>
            <input id="postagePrice" type="number" min="0" step="0.01" placeholder="0.00" />
          </div>
        </div>
        <div class="price-summary" style="margin-top: 10px;">
          <span id="inPersonPrice">In-person price: 0.00 GBP</span>
          <span id="onlinePrice">Online price: 0.00 GBP</span>
        </div>
        <div class="table-wrap" style="margin-top: 12px;">
          <table class="pricing-table">
            <thead>
              <tr>
                <th>Size</th>
                <th>Cost to make</th>
                <th>Sale price</th>
                <th>Postage price</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody id="sizePricingBody"></tbody>
          </table>
        </div>
        <div class="actions" style="margin-top: 12px;">
          <button class="btn secondary" id="savePricingBtn" type="button">Save Pricing</button>
        </div>
        <div style="margin-top: 12px;">
          <label>Listings (auto from URLs)</label>
          <div class="listing-group" id="listingGroup"></div>
          <div class="listing-links" id="listingLinks"></div>
        </div>
        <div class="url-grid">
          <div>
            <label for="facebookUrl">Facebook URL</label>
            <input id="facebookUrl" type="url" placeholder="https://..." />
          </div>
          <div>
            <label for="tiktokUrl">TikTok URL</label>
            <input id="tiktokUrl" type="url" placeholder="https://..." />
          </div>
          <div>
            <label for="ebayUrl">Ebay URL</label>
            <input id="ebayUrl" type="url" placeholder="https://..." />
          </div>
          <div>
            <label for="etsyUrl">Etsy URL</label>
            <input id="etsyUrl" type="url" placeholder="https://..." />
          </div>
        </div>
        <div class="actions" style="margin-top: 16px;">
          <button class="btn ghost" id="openFolderBtn" type="button">Open Folder</button>
          <button class="btn ghost" id="renameBtn" type="button">Rename Folder</button>
          <button class="btn secondary" id="saveDetailsBtn" type="button">Save Details</button>
        </div>
        <div class="status" id="status"></div>
      </section>

      <section class="card">
        <label for="readme">README.md</label>
        <textarea id="readme"></textarea>
        <div class="actions" style="margin-top: 12px;">
          <button class="btn" id="saveReadmeBtn" type="button">Save README</button>
        </div>
      </section>

      <section class="card">
        <h2 style="margin-top:0;color:#0a663b;">Media</h2>
        <div class="media-grid" id="mediaGrid"></div>
      </section>

      <section class="card">
        <h2 style="margin-top:0;color:#0a663b;">3MF Files</h2>
        <div class="file-list" id="threeMfList"></div>
      </section>

      <section class="card" id="ukcaPackSection" hidden>
        <details class="ukca-pack" id="ukcaPackDetails">
          <summary>UKCA Pack</summary>
          <div class="ukca-pack-body">
            <div class="ukca-pack-actions">
              <button class="btn ghost" id="printUkcaBtn" type="button">Print UKCA Pack</button>
            </div>
            <div class="file-list" id="ukcaPackList"></div>
          </div>
        </details>
      </section>

      <section class="card">
        <h2 style="margin-top:0;color:#0a663b;">Upload Media / 3MF</h2>
        <div class="upload-zone" id="uploadZone">
          <strong>Drop files here</strong> or click to choose
        </div>
        <input id="uploadInput" type="file" multiple hidden />
      </section>
    </main>

    <dialog id="ukcaDialog">
      <form id="ukcaForm">
        <div class="dialog-header">
          <strong>Create UKCA Pack</strong>
        </div>
        <div class="dialog-body">
          <div>
            <label for="ukcaProductName">Product name</label>
            <input id="ukcaProductName" type="text" required />
          </div>
          <div>
            <label for="ukcaSku">SKU</label>
            <input id="ukcaSku" type="text" />
          </div>
          <div>
            <label for="ukcaMaterials">Materials</label>
            <input id="ukcaMaterials" type="text" placeholder="PLA / PETG" />
          </div>
          <div>
            <label for="ukcaIntendedAge">Intended age</label>
            <input id="ukcaIntendedAge" type="text" placeholder="3+" />
          </div>
          <div>
            <label for="ukcaManufacturer">Manufacturer</label>
            <input id="ukcaManufacturer" type="text" placeholder="GeekyThingsUK" />
          </div>
          <div>
            <label for="ukcaAddress">Manufacturer address</label>
            <input id="ukcaAddress" type="text" placeholder="United Kingdom" />
          </div>
          <div>
            <label for="ukcaTester">Tester</label>
            <input id="ukcaTester" type="text" placeholder="Dan Robinson" />
          </div>
          <div>
            <label for="ukcaTestDate">Test date</label>
            <input id="ukcaTestDate" type="date" />
          </div>
          <div>
            <label for="ukcaNotes">Notes</label>
            <textarea id="ukcaNotes" rows="3" placeholder="Optional notes..."></textarea>
          </div>
        </div>
        <div class="dialog-actions">
          <button class="btn ghost" type="button" onclick="document.getElementById('ukcaDialog').close()">Cancel</button>
          <button class="btn" type="submit">Create UKCA Pack</button>
        </div>
      </form>
    </dialog>
</template>
