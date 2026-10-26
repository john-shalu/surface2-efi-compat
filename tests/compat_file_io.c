// SPDX-License-Identifier: GPL-2.0-only
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned long efi_status_t;
typedef uint32_t u32;
typedef uint64_t u64;
typedef unsigned short efi_char16_t;
#define CONFIG_EFI_SURFACE2_COMPAT 1
#ifndef CONFIG_EFI_SURFACE2_BOOT_LOG
#define CONFIG_EFI_SURFACE2_BOOT_LOG 1
#endif
#define IS_ENABLED(x) (x)
#define EFI_SUCCESS 0UL
#define EFI_INVALID_PARAMETER 0x80000002UL
#define EFI_BAD_BUFFER_SIZE 0x80000004UL
#define EFI_DEVICE_ERROR 0x80000007UL
#define EFI_NOT_FOUND 0x8000000eUL
#define EFI_WRITE_PROTECTED 0x80000008UL
#define EFI_LOADER_DATA 2
#define EFI_FILE_MODE_READ 1ULL
#define EFI_FILE_MODE_WRITE 2ULL
#define efi_bs_call(f,...) mock_##f(__VA_ARGS__)
#define efi_call_proto(p,f,...) ((p)->f(p, ##__VA_ARGS__))
struct file;
typedef struct file efi_file_protocol_t;
struct file {
 efi_status_t (*open)(struct file *,struct file **,const efi_char16_t *,u64,u64);
 efi_status_t (*close)(struct file *);
 efi_status_t (*read)(struct file *,unsigned long *,void *);
 efi_status_t (*write)(struct file *,unsigned long *,void *);
 efi_status_t (*set_position)(struct file *,u64);
 efi_status_t (*flush)(struct file *);
 int kind;
};
typedef struct {void *load_options;u32 load_options_size;void *image_base;} efi_loaded_image_t;
struct finfo {efi_char16_t filename[256];};
static efi_file_protocol_t volume,file,logfile;
static const char *input;
static unsigned long input_size,position,chunk;
static u64 log_position;
static int opens,closes,allocs,reads,all_writes;
static bool eof_early,missing,write_fail;
static char records[2048];
static bool has(const efi_char16_t *s,const char *needle) {
 char a[300];unsigned i=0;while(s[i]&&i<299){a[i]=(char)s[i];i++;}a[i]=0;return strstr(a,needle)!=NULL;
}
static efi_status_t open_file(struct file *v,struct file **p,const efi_char16_t *name,u64 mode,u64 attr) {
 (void)v;(void)mode;(void)attr;opens++;
 if(has(name,"boot-stage.log")){*p=&logfile;return EFI_SUCCESS;}
 if(missing){opens--;return EFI_NOT_FOUND;}*p=&file;return EFI_SUCCESS;
}
static efi_status_t close_file(struct file *f){(void)f;closes++;return EFI_SUCCESS;}
static efi_status_t read_file(struct file *f,unsigned long *n,void *p){
 (void)f;reads++;if(eof_early){*n=0;return EFI_SUCCESS;}
 if(*n>input_size-position)*n=input_size-position;if(chunk&&*n>chunk)*n=chunk;
 memcpy(p,input+position,*n);position+=*n;return EFI_SUCCESS;
}
static efi_status_t write_file(struct file *f,unsigned long *n,void *p){
 (void)f;all_writes++;if(write_fail)return EFI_WRITE_PROTECTED;
 assert(log_position+*n<=sizeof(records));memcpy(records+log_position,p,*n);return EFI_SUCCESS;
}
static efi_status_t set_position(struct file *f,u64 p){(void)f;log_position=p;return EFI_SUCCESS;}
static efi_status_t flush_file(struct file *f){(void)f;return EFI_SUCCESS;}
static efi_status_t efi_open_volume(efi_loaded_image_t *im,struct file **p){(void)im;*p=&volume;opens++;return EFI_SUCCESS;}
static efi_status_t efi_open_file(struct file *v,struct finfo *fi,struct file **p,unsigned long *size){
 efi_status_t s=open_file(v,p,fi->filename,1,0);*size=input_size;return s;
}
static efi_status_t mock_allocate_pool(int type,unsigned long size,void **p){(void)type;*p=malloc(size);assert(*p);allocs++;return EFI_SUCCESS;}
static efi_status_t mock_free_pool(void *p){free(p);allocs--;return EFI_SUCCESS;}
#include "surface2-file-compat.c"
static void reset(void){
 volume=(struct file){.open=open_file,.close=close_file};
 file=(struct file){.close=close_file,.read=read_file};
 logfile=(struct file){.close=close_file,.write=write_file,.set_position=set_position,.flush=flush_file};
 input="root=/dev/mmcblk1p2 rw";input_size=strlen(input);position=chunk=0;
 opens=closes=allocs=reads=0;eof_early=missing=write_fail=false;memset(records,' ',sizeof(records));
}
static void test(const char *name,efi_status_t expect,const char *text,efi_loaded_image_t *im){
 void *original=im->load_options;u32 original_size=im->load_options_size;
 efi_status_t s=efi_surface2_prepare(im);assert(s==expect);
 if(text){efi_char16_t *p=im->load_options;for(unsigned i=0;;i++){assert(p[i]==(unsigned char)text[i]);if(!text[i])break;}}
 if(expect!=EFI_SUCCESS)assert(im->load_options==original&&im->load_options_size==original_size);
 efi_surface2_cleanup(im);assert(im->load_options==original&&im->load_options_size==original_size);assert(opens==closes);assert(allocs==0);
 printf("PASS %s\n",name);
}
int main(void){
 efi_loaded_image_t im={.image_base=(void *)0x82000000};
 reset();test("no-final-newline",0,input,&im);
 reset();input="root=x rw\r\n";input_size=strlen(input);test("CRLF",0,"root=x rw",&im);
 reset();chunk=3;test("partial-read",0,input,&im);assert(reads>1);
 reset();eof_early=true;test("early-EOF",EFI_DEVICE_ERROR,NULL,&im);
 reset();input_size=2049;test("too-large",EFI_BAD_BUFFER_SIZE,NULL,&im);
 reset();input_size=0;test("empty",EFI_BAD_BUFFER_SIZE,NULL,&im);
 reset();input=" \t\r\n";input_size=strlen(input);test("whitespace-only",EFI_INVALID_PARAMETER,NULL,&im);
 reset();input="root=x\nrw";input_size=strlen(input);test("embedded-newline",EFI_INVALID_PARAMETER,NULL,&im);
 reset();input="\xef\xbb\xbfroot=x";input_size=strlen(input);test("non-ASCII",EFI_INVALID_PARAMETER,NULL,&im);
 reset();missing=true;test("missing-file",EFI_NOT_FOUND,NULL,&im);
 reset();write_fail=true;if(CONFIG_EFI_SURFACE2_BOOT_LOG)test("log-not-writable",EFI_WRITE_PROTECTED,NULL,&im);else test("logging-disabled-no-write",0,input,&im);
 reset();efi_char16_t opts[]={'r','w',0};im.load_options=opts;im.load_options_size=sizeof(opts);test("existing-LoadOptions",0,"rw",&im);assert(opens==0);im.load_options=NULL;im.load_options_size=0;
 if(!CONFIG_EFI_SURFACE2_BOOT_LOG)assert(all_writes==0);puts("ALL 12 COMPATIBILITY TESTS PASSED; NO LEAKED FILE HANDLES OR ALLOCATIONS");return 0;
}
