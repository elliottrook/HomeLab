// SPDX-License-Identifier: GPL-2.0-only
/*
 * One-shot B60 VF BAR preparation for the HomeLab Proxmox host.
 *
 * This proof candidate must load before xe.  It reduces only the disabled
 * SR-IOV VF LMEM BAR template for Intel device 8086:e211 to the smallest size
 * advertised by the device.  xe can then attempt its normal PF LMEM BAR resize
 * without a 48 GiB VF reservation occupying the bridge aperture.
 */

#include <linux/bitops.h>
#include <linux/init.h>
#include <linux/module.h>
#include <linux/pci.h>

#define B60_DEVICE_ID 0xe211
#define B60_DOMAIN 0
#define B60_BUS 4
#define B60_DEVFN PCI_DEVFN(0, 0)
#define B60_VF_LMEM_BAR (PCI_IOV_RESOURCES + 2)

static struct pci_dev *b60;

static int __init b60_vfbar_init(void)
{
	resource_size_t current_size, target_size;
	u32 sizes;
	int size, ret;

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

	sizes = pci_rebar_get_possible_sizes(b60, B60_VF_LMEM_BAR);
	if (!sizes) {
		pr_err("b60_vfbar: VF LMEM BAR is not resizable\n");
		ret = -EOPNOTSUPP;
		goto err_put;
	}

	size = __ffs(sizes);
	target_size = pci_rebar_size_to_bytes(size);
	current_size = pci_resource_len(b60, B60_VF_LMEM_BAR);

	if (current_size == target_size) {
		pr_info("b60_vfbar: VF LMEM BAR already %pa bytes\n",
			&target_size);
		return 0;
	}

	ret = pci_iov_vf_bar_set_size(b60, B60_VF_LMEM_BAR, size);
	if (ret) {
		pr_err("b60_vfbar: resize from %pa to %pa bytes failed: %d\n",
		       &current_size, &target_size, ret);
		goto err_put;
	}

	pr_info("b60_vfbar: reduced disabled VF LMEM BAR from %pa to %pa bytes\n",
		&current_size, &target_size);
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
