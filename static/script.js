// ----------------- SHOW / HIDE SECTIONS -----------------
function showSection(sectionId) {
    const sections = ["dashboard-container", "browse", "claimSection", "myClaims"];
    
    // Hide all sections
    sections.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = "none";
    });

    // Show the requested section
    const target = document.getElementById(sectionId);
    if (target) target.style.display = "block";
}

// ----------------- CLOSE MODALS FUNCTIONS -----------------
function closeReplyModal() {
    document.getElementById('replyModal').style.display = 'none';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// ----------------- DOM CONTENT LOADED -----------------
document.addEventListener("DOMContentLoaded", function () {

    // ----------------- GET MAIN ELEMENTS -----------------
    const dashboard = document.getElementById("dashboard-container");
    const browseSection = document.getElementById("browse");
    const claimSection = document.getElementById("claimSection");
    const myClaimsSection = document.getElementById("myClaims");
    const reportModal = document.getElementById("reportModal");

    // Hide Browse, Claim, My Claims initially
    if (browseSection) browseSection.style.display = "none";
    if (claimSection) claimSection.style.display = "none";
    if (myClaimsSection) myClaimsSection.style.display = "none";

    // ----------------- REPORT MODAL -----------------
    const lostTab = document.getElementById("lostTab");
    const foundTab = document.getElementById("foundTab");
    const formTitle = document.getElementById("formTitle");

    window.openModal = function(type) {
        if (reportModal) reportModal.classList.add("show");
        switchTab(type === "lost" ? "lost" : "found");
        const reportForm = document.getElementById("reportForm");
        if (reportForm) reportForm.reset();
        if (dashboard) dashboard.style.filter = 'blur(5px)';
    };

    window.closeModal = function() {
        if (reportModal) reportModal.classList.remove("show");
        if (dashboard) dashboard.style.filter = 'none';
    };

    window.switchTab = function(tabName) {
        if (!lostTab || !foundTab || !formTitle) return;
        const itemKindInput = document.getElementById("itemKind");
        const reportForm = document.getElementById("reportForm");
        if (reportForm) reportForm.reset();

        if (tabName === "lost") {
            lostTab.classList.add("active");
            foundTab.classList.remove("active");
            formTitle.textContent = "Report Lost Item";
            if (itemKindInput) itemKindInput.value = "Lost";
        } else {
            lostTab.classList.remove("active");
            foundTab.classList.add("active");
            formTitle.textContent = "Report Found Item";
            if (itemKindInput) itemKindInput.value = "Found";
        }
    };

    // ----------------- BROWSE SECTION -----------------
    window.openBrowsePage = function() {
        showSection('browse');
    };

    window.backToDashboard = function() {
        showSection('dashboard-container');
    };

    window.filterItems = function() {
        const searchValue = document.getElementById("searchBox").value.toLowerCase();
        const categoryValue = document.getElementById("categoryFilter").value.toLowerCase();
        const items = document.querySelectorAll("#itemsGrid .step");

        items.forEach(item => {
            const title = item.dataset.title.toLowerCase();
            const description = item.dataset.description.toLowerCase();
            const location = item.dataset.location.toLowerCase();
            const itemCategory = item.dataset.category.toLowerCase();

            if ((title.includes(searchValue) || description.includes(searchValue) || location.includes(searchValue) || searchValue === "") &&
                (itemCategory === categoryValue || categoryValue === "")) {
                item.style.display = "block";
            } else {
                item.style.display = "none";
            }
        });
    };

    // ----------------- CLAIM SECTION -----------------
    const claimForm = document.getElementById("claimForm");
    if (claimForm) {
        claimForm.addEventListener("submit", function(e) {
            e.preventDefault();
            const message = document.getElementById("message").value.trim();
            if (!message) {
                alert("Please fill all fields");
                return;
            }
            claimForm.submit();
        });
    }

    document.querySelectorAll('.claim-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('claimItemId').value = btn.dataset.itemId;
            document.getElementById('claimItemTitle').textContent = btn.dataset.itemTitle;
            document.getElementById('claimItemDescription').textContent = btn.dataset.itemDescription;
            document.getElementById('claimItemLocation').textContent = btn.dataset.itemLocation;
            showSection('claimSection');
        });
    });

    const backToBrowseBtn = document.getElementById('backToBrowse');
    if (backToBrowseBtn) {
        backToBrowseBtn.addEventListener('click', () => {
            showSection('browse');
        });
    }

    window.closeClaimModal = function() {
        showSection('dashboard-container');
    };

    // ----------------- REPORT FORM VALIDATION -----------------
    const reportForm = document.getElementById("reportForm");
    if (reportForm) {
        reportForm.addEventListener("submit", function(e) {
            const title = reportForm.title.value.trim();
            const category = reportForm.category.value.trim();
            const date = reportForm.date.value.trim();
            const description = reportForm.description.value.trim();
            const location = reportForm.location.value.trim();
            const contact_email = reportForm.contact_email.value.trim();
            const contact_phone = reportForm.contact_phone.value.trim();

            if (!title || !category || !date || !description || !location || !contact_email || !contact_phone) {
                e.preventDefault();
                alert("Please fill all required fields including contact info");
            }
        });
    }

    // ----------------- REPLY MODAL -----------------
    document.querySelectorAll('.reply-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const claimId = btn.dataset.claimId;
            document.getElementById('replyClaimId').value = claimId;
            document.getElementById('replyModal').style.display = 'flex';
        });
    });

    document.getElementById('closeReplyModal').addEventListener('click', closeReplyModal);
    document.getElementById('cancelReply').addEventListener('click', closeReplyModal);

    // ----------------- REQUEST INFO MODAL -----------------
    document.querySelectorAll('.info').forEach(btn => {
    btn.addEventListener('click', () => {
        const claimId = btn.dataset.claimId;
        document.getElementById('requestInfoClaimId').value = claimId;
        document.getElementById('requestInfoModal').style.display = 'flex';

        // Update status immediately
        fetch(`/update-status/${claimId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Need Info' })
})
.then(res => res.json())   // <-- add this line to parse JSON response
.then(data => {
    if (data.success) {     // <-- check if backend responded with success
        const statusSpan = btn.closest('tr').querySelector('.status');
        if (statusSpan) {
            statusSpan.textContent = 'Need Info';
            statusSpan.className = 'status need-info';
        }
    } else {
        alert('Status update failed');
    }
})
.catch(err => console.error(err));


    });
});



    // ----------------- OUTSIDE CLICK HANDLER -----------------
    window.addEventListener('click', function(event) {
        const replyModal = document.getElementById('replyModal');
        const requestInfoModal = document.getElementById('requestInfoModal');
        const reportModal = document.getElementById('reportModal');
        const claimSection = document.getElementById('claimSection');

        if (event.target === replyModal) closeReplyModal();
        if (event.target === requestInfoModal) closeModal('requestInfoModal');
        if (event.target === reportModal) closeModal();
        if (event.target === claimSection) closeClaimModal();
    });
const backFromMyClaimsBtn = document.getElementById('backFromMyClaims');
if (backFromMyClaimsBtn) {
    backFromMyClaimsBtn.addEventListener('click', () => {
        showSection('dashboard-container');
    });
}
setTimeout(() => {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => alert.remove());
}, 4000);


});


