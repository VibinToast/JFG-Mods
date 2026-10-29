# A mod for Jet Force Gemini: Recompiled: MIPS code built with clang and lld, then turned into an .nrm by N64Recomp's
# RecompModTool (make nrm). Based on the Snap64RecompModTemplate Makefile.
#
# The game's symbol files (jfg.us.syms.toml, jfg.us.datasyms.toml) come from the JFGRecompSyms repo: point SYMS at a
# checkout of it (make syms copies them into syms/, which git ignores).

BUILD_DIR := build
CC        := clang
LD        := ld.lld
MODTOOL   ?= $(HOME)/tools/modkit/N64Recomp/build/RecompModTool
SYMS      ?= ../../JFGRecompSyms

TARGET   := $(BUILD_DIR)/mod.elf
LDSCRIPT := mod.ld
ARCHFLAGS := -target mips -mips2 -mabi=32 -O2 -G0 -mno-abicalls -mno-odd-spreg -mno-check-zero-division \
             -fomit-frame-pointer -ffast-math -fno-unsafe-math-optimizations -fno-builtin-memset -fno-builtin-memcpy \
             -fno-builtin-memmove -fno-builtin-bcopy -funsigned-char -fno-builtin-sinf -fno-builtin-cosf
WARNFLAGS := -Wall -Wextra -Wno-unused-parameter -Wno-unknown-pragmas -Wno-unused-variable -Wno-missing-braces \
             -Wno-unsupported-floating-point-opt -Werror=section -Wno-visibility
CFLAGS   := $(ARCHFLAGS) $(WARNFLAGS) -D_LANGUAGE_C -nostdinc -ffunction-sections
CPPFLAGS := -I include
LDFLAGS  := -nostdlib -T $(LDSCRIPT) -Map $(BUILD_DIR)/mod.map --unresolved-symbols=ignore-all --emit-relocs -e 0 \
            --no-nmagic -gc-sections

C_SRCS := $(wildcard src/*.c)
C_OBJS := $(addprefix $(BUILD_DIR)/, $(C_SRCS:.c=.o))

all: $(TARGET)

$(TARGET): $(C_OBJS) $(LDSCRIPT)
	$(LD) $(C_OBJS) $(LDFLAGS) -o $@

$(BUILD_DIR)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) $(CPPFLAGS) $< -MMD -MF $(@:.o=.d) -c -o $@

syms/jfg.us.syms.toml syms/jfg.us.datasyms.toml:
	@mkdir -p syms
	cp $(SYMS)/jfg.us.syms.toml $(SYMS)/jfg.us.datasyms.toml syms/

syms: syms/jfg.us.syms.toml

nrm: $(TARGET) syms/jfg.us.syms.toml thumb.png
	$(MODTOOL) mod.toml $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)

-include $(C_OBJS:.o=.d)

.PHONY: all nrm syms clean
