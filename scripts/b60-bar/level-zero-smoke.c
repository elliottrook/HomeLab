/* Tiny 4 KiB device-memory roundtrip; no model load or persistent device change. */
#include <level_zero/ze_api.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(call) do { ze_result_t r = (call); if (r != ZE_RESULT_SUCCESS) { \
 fprintf(stderr, "%s failed: 0x%x\n", #call, r); return 1; } } while (0)

int main(void)
{
 uint32_t n = 0;
 CHECK(zeInit(ZE_INIT_FLAG_GPU_ONLY));
 CHECK(zeDriverGet(&n, NULL));
 printf("drivers=%u\n", n);
 if (!n || n > 16) return 1;
 ze_driver_handle_t drivers[16];
 CHECK(zeDriverGet(&n, drivers));
 for (uint32_t i = 0; i < n; i++) {
  uint32_t count = 0;
  CHECK(zeDeviceGet(drivers[i], &count, NULL));
  if (!count || count > 16) continue;
  ze_device_handle_t devices[16];
  CHECK(zeDeviceGet(drivers[i], &count, devices));
  for (uint32_t j = 0; j < count; j++) {
   ze_device_properties_t props = {.stype=ZE_STRUCTURE_TYPE_DEVICE_PROPERTIES};
   CHECK(zeDeviceGetProperties(devices[j], &props));
   printf("device=%s vendor=0x%x device=0x%x\n", props.name, props.vendorId, props.deviceId);
   if (props.vendorId != 0x8086 || props.deviceId != 0xe211) continue;
   ze_context_desc_t cd = {.stype=ZE_STRUCTURE_TYPE_CONTEXT_DESC};
   ze_context_handle_t ctx;
   CHECK(zeContextCreate(drivers[i], &cd, &ctx));
   uint32_t groups = 0;
   CHECK(zeDeviceGetCommandQueueGroupProperties(devices[j], &groups, NULL));
   if (groups > 32) return 1;
   ze_command_queue_group_properties_t gp[32];
   memset(gp, 0, sizeof(gp));
   for (uint32_t k=0; k<groups; k++) gp[k].stype=ZE_STRUCTURE_TYPE_COMMAND_QUEUE_GROUP_PROPERTIES;
   CHECK(zeDeviceGetCommandQueueGroupProperties(devices[j], &groups, gp));
   uint32_t ordinal=0;
   while (ordinal<groups && !(gp[ordinal].flags & ZE_COMMAND_QUEUE_GROUP_PROPERTY_FLAG_COMPUTE)) ordinal++;
   if (ordinal==groups) return 1;
   ze_command_queue_desc_t qd = {.stype=ZE_STRUCTURE_TYPE_COMMAND_QUEUE_DESC,
     .ordinal=ordinal, .index=0, .mode=ZE_COMMAND_QUEUE_MODE_ASYNCHRONOUS};
   ze_command_queue_handle_t queue;
   CHECK(zeCommandQueueCreate(ctx, devices[j], &qd, &queue));
   ze_command_list_desc_t ld = {.stype=ZE_STRUCTURE_TYPE_COMMAND_LIST_DESC, .commandQueueGroupOrdinal=ordinal};
   ze_command_list_handle_t list;
   CHECK(zeCommandListCreate(ctx, devices[j], &ld, &list));
   ze_device_mem_alloc_desc_t ad = {.stype=ZE_STRUCTURE_TYPE_DEVICE_MEM_ALLOC_DESC};
   void *gpu=NULL;
   CHECK(zeMemAllocDevice(ctx, &ad, 4096, 64, devices[j], &gpu));
   unsigned char input[4096], output[4096];
   for (unsigned k=0; k<4096; k++) input[k]=(unsigned char)(k*37+11);
   memset(output,0,sizeof(output));
   CHECK(zeCommandListAppendMemoryCopy(list,gpu,input,sizeof(input),NULL,0,NULL));
   CHECK(zeCommandListAppendBarrier(list,NULL,0,NULL));
   CHECK(zeCommandListAppendMemoryCopy(list,output,gpu,sizeof(output),NULL,0,NULL));
   CHECK(zeCommandListClose(list));
   CHECK(zeCommandQueueExecuteCommandLists(queue,1,&list,NULL));
   CHECK(zeCommandQueueSynchronize(queue,5000000000ULL));
   int passed=!memcmp(input,output,sizeof(input));
   CHECK(zeCommandListDestroy(list));
   CHECK(zeCommandQueueDestroy(queue));
   CHECK(zeMemFree(ctx,gpu));
   CHECK(zeContextDestroy(ctx));
   printf("device_memory_roundtrip_4096_bytes=%s\n",passed?"PASS":"FAIL");
   return passed?0:1;
  }
 }
 return 1;
}
