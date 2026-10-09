
(function () {
    const csrf = document.querySelector('meta[name="csrf-token"]').content;
    const formDistrict = document.getElementById('form_district_id');
    const formSub = document.getElementById('form_sub_district_id');
    const formVillage = document.getElementById('form_village_word_id');
    const formGenerateBtn = document.getElementById('form-generate-btn');
    const filterDistrict = document.getElementById('filter_district_id');
    const filterSub = document.getElementById('filter_sub_district_id');
    const modal = document.getElementById('detect-modal');
    const modalForm = document.getElementById('detect-modal-form');
    const modalTitle = document.getElementById('detect-modal-title');
    const modalSubtitle = document.getElementById('detect-modal-subtitle');
    const modalSubmit = document.getElementById('detect-modal-submit');
    const modalCancel = document.getElementById('detect-modal-cancel');
    const processingOverlay = document.getElementById('processing-overlay');
    const processingTitle = document.getElementById('processing-title');
    const detectBase = "https:\/\/generate.snsies.com\/village-words";
    const defaultProvider = "google";
    const defaultUseAi = "1";
    let detectSubmitting = false;
    let detectMode = 'generate';

    function fillSelect(select, rows, placeholder, valueKey, labelFn) {
        select.innerHTML = '';
        const opt0 = document.createElement('option');
        opt0.value = '';
        opt0.textContent = placeholder;
        select.appendChild(opt0);
        rows.forEach(function (row) {
            const opt = document.createElement('option');
            opt.value = row[valueKey];
            opt.textContent = labelFn(row);
            select.appendChild(opt);
        });
    }

    async function loadSubDistricts(districtId, targetSelect, keepValue) {
        fillSelect(targetSelect, [], 'Select sub-district', 'id', function () { return ''; });
        if (!districtId) return;
        const res = await fetch("https:\/\/generate.snsies.com\/api\/sub-districts" + '?district_id=' + encodeURIComponent(districtId), {
            headers: { 'Accept': 'application/json', 'X-CSRF-TOKEN': csrf }
        });
        const json = await res.json();
        fillSelect(targetSelect, json.data || [], 'Select sub-district', 'id', function (r) { return r.sub_district_name; });
        if (keepValue) targetSelect.value = String(keepValue);
    }

    async function loadVillages(subDistrictId, targetSelect, keepValue) {
        fillSelect(targetSelect, [], 'Select village', 'id', function () { return ''; });
        if (!subDistrictId) return;
        const res = await fetch("https:\/\/generate.snsies.com\/api\/village-options" + '?sub_district_id=' + encodeURIComponent(subDistrictId), {
            headers: { 'Accept': 'application/json', 'X-CSRF-TOKEN': csrf }
        });
        const json = await res.json();
        fillSelect(targetSelect, json.data || [], 'Select village', 'id', function (r) {
            return r.name + ' (' + r.code + ')';
        });
        if (keepValue) targetSelect.value = String(keepValue);
    }

    function setRadio(name, value) {
        const el = modalForm.querySelector('input[name="' + name + '"][value="' + value + '"]');
        if (el) el.checked = true;
    }

    function openDetectModal(villageId, villageName, mode) {
        if (detectSubmitting) return;
        detectMode = mode === 'update' ? 'update' : 'generate';
        modalForm.action = detectBase + '/' + villageId + '/detect';
        const isUpdate = detectMode === 'update';
        modalTitle.textContent = isUpdate ? 'Update detection' : 'Generate detection';
        modalSubtitle.textContent = (isUpdate ? 'Re-run detection for ' : 'Generate wells for ')
            + (villageName || 'selected village')
            + '. Choose imagery and method.';
        modalSubmit.disabled = false;
        modalCancel.disabled = false;
        modalSubmit.textContent = isUpdate ? 'Update & start' : 'Generate & start';
        setRadio('imagery_provider', defaultProvider || 'google');
        setRadio('use_ai', '0');
        modal.classList.add('open');
    }

    function closeDetectModal() {
        if (detectSubmitting) return;
        modal.classList.remove('open');
    }

    function showProcessingOverlay() {
        processingTitle.textContent = detectMode === 'update' ? 'Updating detection…' : 'Generating detection…';
        processingOverlay.classList.add('open');
        document.body.classList.add('is-processing');
        if (formGenerateBtn) formGenerateBtn.disabled = true;
        document.querySelectorAll('.js-open-detect').forEach(function (btn) {
            btn.disabled = true;
        });
    }

    formDistrict.addEventListener('change', async function () {
        await loadSubDistricts(formDistrict.value, formSub, null);
        fillSelect(formVillage, [], 'Select village', 'id', function () { return ''; });
    });

    formSub.addEventListener('change', async function () {
        await loadVillages(formSub.value, formVillage, null);
    });

    filterDistrict.addEventListener('change', async function () {
        await loadSubDistricts(filterDistrict.value, filterSub, null);
    });

    formGenerateBtn.addEventListener('click', function () {
        if (detectSubmitting) return;
        const id = formVillage.value;
        if (!id) {
            alert('Please select a village.');
            return;
        }
        const name = formVillage.options[formVillage.selectedIndex]
            ? formVillage.options[formVillage.selectedIndex].textContent
            : 'village';
        openDetectModal(id, name, 'generate');
    });

    document.querySelectorAll('.js-open-detect').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (detectSubmitting) return;
            openDetectModal(
                btn.getAttribute('data-village-id'),
                btn.getAttribute('data-village-name'),
                btn.getAttribute('data-mode') || 'generate'
            );
        });
    });

    modalCancel.addEventListener('click', closeDetectModal);
    modal.addEventListener('click', function (e) {
        if (e.target === modal) closeDetectModal();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeDetectModal();
    });

    modalForm.addEventListener('submit', function (e) {
        if (detectSubmitting) {
            e.preventDefault();
            return false;
        }
        if (!modalForm.querySelector('input[name="imagery_provider"]:checked')) {
            alert('Please choose imagery for detection.');
            e.preventDefault();
            return false;
        }
        if (!modalForm.querySelector('input[name="use_ai"]:checked')) {
            alert('Please choose a detection method.');
            e.preventDefault();
            return false;
        }

        detectSubmitting = true;
        modalSubmit.disabled = true;
        modalCancel.disabled = true;
        modal.classList.remove('open');
        showProcessingOverlay();
        return true;
    });

    if (formSub.value) {
        loadVillages(formSub.value, formVillage, null);
    }
})();
