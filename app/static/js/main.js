document.addEventListener('DOMContentLoaded', (event) => {
	const ticketTypeSelect = document.getElementById("ticketTypeSelect");
	const quantityInput = document.getElementById("quantity");
	const amountInput = document.getElementById("amount");

	function updateAmount() {
		const selectedOption = ticketTypeSelect.options[ticketTypeSelect.selectedIndex];
		const price = Number(selectedOption.getAttribute("data_price"));
		const quantity = Number(quantityInput.value);
		amountInput.value = price * quantity;
	}
	ticketTypeSelect.addEventListener('change', updateAmount);
	quantityInput.addEventListener('change', updateAmount);

	// Initial update 
	updateAmount();
});
const sidebarBtn = document.getElementById("sidebar-toggler");
const sidebarWrapper = document.getElementById("sidebar-wrapper");
sidebarBtn.addEventListener('click', () => {
	sidebarWrapper.classList.toggle('open');
});

