// SPDX-License-Identifier: GPL-2.0-only
/*
 * One-shot B60 VF BAR preparation for the HomeLab Proxmox host.
 *
 * This proof candidate must load before xe.  A candidate-only kernel argument
 * first reserves aligned space for the PF BARs.  This helper then selects the
 * full PF LMEM BAR, restores the PF GTT reservation to its hardware size and
 * reduces the disabled SR-IOV VF LMEM BAR template for Intel device 8086:e211.
 */

#include <linux/bitops.h>
#include <linux/init.h>
#include <linux/ioport.h>
#include <linux/module.h>
#include <linux/pci.h>
#include <linux/sizes.h>

#define B60_DEVICE_ID 0xe211
#define B60_DOMAIN 0
#define B60_BUS 4
#define B60_DEVFN PCI_DEVFN(0, 0)
#define B60_PF_GTT_BAR 0
#define B60_PF_LMEM_BAR 2
#define B60_VF_LMEM_BAR (PCI_IOV_RESOURCES + 2)

static struct pci_dev *b60;

static int b60_set_pf_rebar_size(struct pci_dev *pdev, int bar, int size)
{
	u32 ctrl, sizes;
	int i, nbar, pos, ret;

	pos = pci_find_ext_capability(pdev, PCI_EXT_CAP_ID_REBAR);
	if (!pos)
		return -EOPNOTSUPP;

	ret = pci_read_config_dword(pdev, pos + PCI_REBAR_CTRL, &ctrl);
	if (ret)
		return pcibios_err_to_errno(ret);
	nbar = (ctrl & PCI_REBAR_CTRL_NBAR_MASK) >> PCI_REBAR_CTRL_NBAR_SHIFT;

	for (i = 0; i < nbar; i++, pos += 8) {
		ret = pci_read_config_dword(pdev, pos + PCI_REBAR_CTRL, &ctrl);
		if (ret)
			return pcibios_err_to_errno(ret);
		if ((ctrl & PCI_REBAR_CTRL_BAR_IDX) != bar)
			continue;

		ret = pci_read_config_dword(pdev, pos + PCI_REBAR_CAP, &sizes);
		if (ret)
			return pcibios_err_to_errno(ret);
		sizes = (sizes & PCI_REBAR_CAP_SIZES) >> 4;
		if (!(sizes & BIT(size)))
			return -EOPNOTSUPP;

		ctrl &= ~PCI_REBAR_CTRL_BAR_SIZE;
		ctrl |= size << PCI_REBAR_CTRL_BAR_SHIFT;
		ret = pci_write_config_dword(pdev, pos + PCI_REBAR_CTRL, ctrl);
		if (ret)
			return pcibios_err_to_errno(ret);

		ret = pci_read_config_dword(pdev, pos + PCI_REBAR_CTRL, &ctrl);
		if (ret)
			return pcibios_err_to_errno(ret);
		if (((ctrl & PCI_REBAR_CTRL_BAR_SIZE) >>
		     PCI_REBAR_CTRL_BAR_SHIFT) != size)
			return -EIO;
		return 0;
	}

	return -ENOENT;
}

static int __init b60_vfbar_init(void)
{
	struct resource *gtt_resource, *lmem_resource, *vf_resource;
	resource_size_t current_size, target_size, total_size;
	u32 sizes;
	int lmem_size, ret, size, total_vfs;

	b60 = pci_get_domain_bus_and_slot(B60_DOMAIN, B60_BUS, B60_DEVFN);
	if (!b60)
		return -ENODEV;
	if (b60->vendor != PCI_VENDOR_ID_INTEL || b60->device != B60_DEVICE_ID) {
		pr_err("b60_vfbar: 0000:04:00.0 is not Intel device 8086:e211\n");
		ret = -ENODEV;
		goto err_put;
	}

	if (pci_num_vf(b60)) {
		pr_err("b60_vfbar: refusing resize while VFs are enabled\n");
		ret = -EBUSY;
		goto err_put;
	}

	gtt_resource = &b60->resource[B60_PF_GTT_BAR];
	lmem_resource = &b60->resource[B60_PF_LMEM_BAR];
	if (resource_size(gtt_resource) != SZ_32G ||
	    resource_size(lmem_resource) != SZ_32G ||
	    !IS_ALIGNED(gtt_resource->start, SZ_32G) ||
	    !IS_ALIGNED(lmem_resource->start, SZ_32G)) {
		pr_err("b60_vfbar: required 32 GiB aligned PF reservations are absent\n");
		ret = -EINVAL;
		goto err_put;
	}

	sizes = pci_rebar_get_possible_sizes(b60, B60_PF_LMEM_BAR);
	lmem_size = pci_rebar_bytes_to_size(SZ_32G);
	if (!(sizes & BIT(lmem_size))) {
		pr_err("b60_vfbar: PF LMEM BAR does not advertise 32 GiB\n");
		ret = -EOPNOTSUPP;
		goto err_put;
	}

	ret = b60_set_pf_rebar_size(b60, B60_PF_LMEM_BAR, lmem_size);
	if (ret) {
		pr_err("b60_vfbar: PF LMEM BAR resize to 32 GiB failed: %d\n", ret);
		goto err_put;
	}

	ret = adjust_resource(gtt_resource, gtt_resource->start, SZ_16M);
	if (ret) {
		pr_err("b60_vfbar: PF GTT reservation restore to 16 MiB failed: %d\n",
		       ret);
		goto err_put;
	}

	sizes = pci_rebar_get_possible_sizes(b60, B60_VF_LMEM_BAR);
	if (!sizes) {
		pr_err("b60_vfbar: VF LMEM BAR is not resizable\n");
		ret = -EOPNOTSUPP;
		goto err_put;
	}

	size = __ffs(sizes);
	target_size = pci_rebar_size_to_bytes(size);
	vf_resource = &b60->resource[B60_VF_LMEM_BAR];
	current_size = resource_size(vf_resource);
	total_vfs = pci_sriov_get_totalvfs(b60);
	if (!total_vfs || target_size > RESOURCE_SIZE_MAX / total_vfs) {
		pr_err("b60_vfbar: invalid total VF resource size\n");
		ret = -EINVAL;
		goto err_put;
	}
	total_size = target_size * total_vfs;

	if (current_size == total_size) {
		pr_info("b60_vfbar: VF LMEM reservation already %pa bytes\n",
			&total_size);
		return 0;
	}

	ret = pci_iov_vf_bar_set_size(b60, B60_VF_LMEM_BAR, size);
	if (ret) {
		pr_err("b60_vfbar: resize from %pa to %pa bytes failed: %d\n",
		       &current_size, &target_size, ret);
		goto err_put;
	}

	ret = adjust_resource(vf_resource, vf_resource->start, total_size);
	if (ret) {
		pr_err("b60_vfbar: reservation resize from %pa to %pa bytes failed: %d\n",
		       &current_size, &total_size, ret);
		goto err_put;
	}

	pr_info("b60_vfbar: set PF LMEM BAR to 32 GiB, restored PF GTT "
		 "reservation to 16 MiB, and reduced disabled VF LMEM BAR to "
		 "%pa bytes per VF and reservation from %pa to %pa bytes\n",
		&target_size, &current_size, &total_size);
	return 0;

err_put:
	pci_dev_put(b60);
	b60 = NULL;
	return ret;
}

static void __exit b60_vfbar_exit(void)
{
	if (b60)
		pci_dev_put(b60);
}

module_init(b60_vfbar_init);
module_exit(b60_vfbar_exit);

MODULE_AUTHOR("HomeLab B60 investigation");
MODULE_DESCRIPTION("Prepare the disabled Intel B60 VF LMEM BAR before xe loads");
MODULE_LICENSE("GPL");
