import discord
from discord.ext import commands
import aiohttp
import asyncio
import json
import random
import string
import datetime
from github import Github
import os

# ===============================
# 🚀 CONFIG CHO RAILWAY
# ===============================
print("🚄 Đang khởi động trên Railway...")

# Cấu hình từ biến môi trường
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'cacdai1234/AIMBOTLOAD-APIKEY')
JSON_FILE_PATH = os.getenv('JSON_FILE_PATH', 'auth-data.json')
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '1395096403017072660,1395096403017072660').split(',')]

# Kiểm tra biến môi trường
if not DISCORD_TOKEN:
    print("❌ LỖI: DISCORD_TOKEN không được tìm thấy!")
    exit(1)

if not GITHUB_TOKEN:
    print("❌ LỖI: GITHUB_TOKEN không được tìm thấy!")
    exit(1)

print("✅ Đã load tất cả environment variables")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

class KeyManager:
    def __init__(self, github_token, repo_name):
        self.g = Github(github_token)
        self.repo = self.g.get_repo(repo_name)
    
    def generate_key(self, length=16):
        """Tạo key ngẫu nhiên"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    async def get_current_json(self):
        """Lấy nội dung JSON hiện tại từ GitHub"""
        try:
            contents = self.repo.get_contents(JSON_FILE_PATH)
            current_data = json.loads(contents.decoded_content.decode())
            return current_data
        except Exception as e:
            print(f"⚠️ Lỗi khi get JSON: {e}")
            return []
    
    async def update_json(self, new_data):
        """Cập nhật JSON lên GitHub"""
        try:
            contents = self.repo.get_contents(JSON_FILE_PATH)
            new_json = json.dumps(new_data, indent=2, ensure_ascii=False)
            self.repo.update_file(contents.path, "Update keys", new_json, contents.sha)
            return True
        except Exception as e:
            print(f"❌ Lỗi update GitHub: {e}")
            return False
    
    def calculate_expiry_date(self, days=30):
        """Tính ngày hết hạn"""
        return (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat()
    
    def get_expired_keys(self, keys_data):
        """Lấy danh sách key đã hết hạn"""
        now = datetime.datetime.utcnow()
        expired_keys = []
        
        for key in keys_data:
            if key.get('expires'):
                expiry_date = datetime.datetime.fromisoformat(key['expires'].replace('Z', ''))
                if expiry_date < now:
                    expired_keys.append(key)
        
        return expired_keys

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} đã sẵn sàng trên Railway!')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'👥 Số server: {len(bot.guilds)}')
    print(f'🚄 Đang chạy trên Railway - 24/7!')
    print(f'⏰ Start time: {datetime.datetime.now()}')
    
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!menu | Railway 24/7"))

def is_admin():
    """Check xem user có phải admin không"""
    async def predicate(ctx):
        return ctx.author.id in ADMIN_IDS
    return commands.check(predicate)

# ===============================
# 🎯 LỆNH TẠO KEY
# ===============================

@bot.command()
@is_admin()
async def taokey(ctx, key_type: str, amount: int = 1, days: int = 30):
    """Tạo key với loại và số lượng tùy chọn"""
    valid_types = ["single", "multi", "unlimited"]
    
    if key_type.lower() not in valid_types:
        await ctx.send(f"❌ Loại key không hợp lệ! Chọn: {', '.join(valid_types)}")
        return
    
    await ctx.send(f"🔄 Đang tạo {amount} key {key_type}...")
    
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    new_keys = []
    for i in range(amount):
        new_key = {
            "key": manager.generate_key(),
            "hwid": "",
            "type": key_type,
            "expires": manager.calculate_expiry_date(days) if key_type != "unlimited" else None
        }
        
        if key_type == "unlimited":
            new_key["unlimited"] = True
        
        new_keys.append(new_key)
        current_data.append(new_key)
    
    if await manager.update_json(current_data):
        embed = discord.Embed(title="✅ Tạo Keys Thành Công", color=0x00ff00)
        embed.add_field(name="Số lượng", value=f"{amount} keys", inline=True)
        embed.add_field(name="Loại", value=key_type.capitalize(), inline=True)
        if key_type != "unlimited":
            embed.add_field(name="Hạn", value=f"{days} ngày", inline=True)
        
        keys_list = "\n".join([f"`{key['key']}`" for key in new_keys[:3]])
        if len(new_keys) > 3:
            keys_list += f"\n... và {len(new_keys) - 3} keys khác"
        
        embed.add_field(name="Keys đã tạo", value=keys_list, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Lỗi khi tạo keys!")

# ===============================
# 🗑️ LỆNH XÓA KEY
# ===============================

@bot.command()
@is_admin()
async def xoakey(ctx, *keys):
    """Xóa một hoặc nhiều key khỏi hệ thống"""
    if not keys:
        await ctx.send("📝 **Hướng dẫn xóa nhiều key:**\n"
                      "Cách 1: `!xoakey KEY1 KEY2 KEY3` (cách nhau bằng khoảng trắng)\n"
                      "Cách 2: Gửi danh sách keys (mỗi key một dòng) sau khi gõ lệnh:\n"
                      "```\nKEY1\nKEY2\nKEY3\n...\n```\n"
                      "Gửi `hủy` để hủy bỏ.")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            
            if msg.content.lower() == 'hủy':
                await ctx.send("❌ Đã hủy thao tác xóa key.")
                return
            
            keys = [key.strip() for key in msg.content.split('\n') if key.strip()]
            
            if not keys:
                await ctx.send("❌ Không có key nào được cung cấp!")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏰ Hết thời gian nhập danh sách key!")
            return
    
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    if not current_data:
        await ctx.send("📭 Không có key nào trong hệ thống!")
        return
    
    deleted_keys = []
    not_found_keys = []
    new_data = []
    
    for key_obj in current_data:
        if key_obj['key'] in keys:
            deleted_keys.append(key_obj['key'])
        else:
            new_data.append(key_obj)
    
    for key in keys:
        if key not in deleted_keys:
            not_found_keys.append(key)
    
    if not deleted_keys:
        await ctx.send("❌ Không tìm thấy key nào để xóa!")
        return
    
    if len(deleted_keys) > 3:
        embed = discord.Embed(title="⚠️ XÁC NHẬN XÓA NHIỀU KEY", color=0xffa500)
        embed.add_field(name="Số key sẽ xóa", value=f"**{len(deleted_keys)}** keys", inline=False)
        embed.add_field(name="Danh sách key", value="\n".join([f"`{key}`" for key in deleted_keys[:10]]), inline=False)
        if len(deleted_keys) > 10:
            embed.add_field(name="...", value=f"và {len(deleted_keys) - 10} keys khác", inline=False)
        embed.add_field(name="Xác nhận", value="React với ✅ để xóa, ❌ để hủy", inline=False)
        
        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def reaction_check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=reaction_check)
            
            if str(reaction.emoji) != "✅":
                embed_cancel = discord.Embed(title="❌ Đã Hủy", color=0xff0000)
                embed_cancel.add_field(name="Thao tác", value="Đã hủy xóa key", inline=False)
                await confirm_msg.edit(embed=embed_cancel)
                await confirm_msg.clear_reactions()
                return
            else:
                await confirm_msg.delete()
        except asyncio.TimeoutError:
            await confirm_msg.delete()
            await ctx.send("⏰ Hết thời gian xác nhận!")
            return
    
    if await manager.update_json(new_data):
        embed_success = discord.Embed(title="✅ Xóa Key Thành Công", color=0x00ff00)
        embed_success.add_field(name="Đã xóa", value=f"**{len(deleted_keys)}** keys", inline=True)
        
        if not_found_keys:
            embed_success.add_field(name="Không tìm thấy", value=f"**{len(not_found_keys)}** keys", inline=True)
        
        if deleted_keys:
            keys_display = "\n".join([f"`{key}`" for key in deleted_keys[:8]])
            if len(deleted_keys) > 8:
                keys_display += f"\n... và {len(deleted_keys) - 8} keys khác"
            embed_success.add_field(name="Keys đã xóa", value=keys_display, inline=False)
        
        if not_found_keys:
            not_found_display = "\n".join([f"`{key}`" for key in not_found_keys[:5]])
            if len(not_found_keys) > 5:
                not_found_display += f"\n... và {len(not_found_keys) - 5} keys khác"
            embed_success.add_field(name="Keys không tồn tại", value=not_found_display, inline=False)
        
        await ctx.send(embed=embed_success)
    else:
        await ctx.send("❌ Lỗi khi xóa key!")

# ===============================
# 🔄 RESET HWID
# ===============================

@bot.command()
@is_admin()
async def resetHWID(ctx, key: str):
    """Reset HWID cho key (dùng khi user đổi máy)"""
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    key_found = False
    for k in current_data:
        if k['key'] == key:
            if k['type'] != 'single':
                await ctx.send("❌ Chỉ có thể reset HWID cho key single!")
                return
            
            old_hwid = k['hwid']
            k['hwid'] = ""  # Reset HWID về trống
            key_found = True
            break
    
    if not key_found:
        await ctx.send("❌ Key không tồn tại!")
        return
    
    if await manager.update_json(current_data):
        embed = discord.Embed(title="✅ Reset HWID Thành Công", color=0x00ff00)
        embed.add_field(name="Key", value=f"`{key}`", inline=False)
        embed.add_field(name="HWID cũ", value=f"`{old_hwid if old_hwid else 'Trống'}`", inline=True)
        embed.add_field(name="HWID mới", value="`Trống` (chưa kích hoạt)", inline=True)
        embed.add_field(name="📝 Lưu ý", value="Key đã được reset và có thể kích hoạt lại trên máy mới", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Lỗi khi reset HWID!")

# ===============================
# 👥 QUẢN LÝ ADMIN
# ===============================

@bot.command()
@is_admin()
async def themuser(ctx, user_id: str):
    """Thêm user vào danh sách admin"""
    try:
        user_id_int = int(user_id)
    except ValueError:
        await ctx.send("❌ ID user không hợp lệ!")
        return
    
    if user_id_int in ADMIN_IDS:
        await ctx.send("❌ User đã có trong danh sách admin!")
        return
    
    # Thêm user mới vào ADMIN_IDS
    ADMIN_IDS.append(user_id_int)
    
    embed = discord.Embed(title="✅ Thêm User Admin Thành Công", color=0x00ff00)
    embed.add_field(name="User ID", value=f"`{user_id_int}`", inline=False)
    embed.add_field(name="Tổng số admin", value=f"**{len(ADMIN_IDS)}** users", inline=True)
    embed.add_field(name="📝 Lưu ý", value="Thay đổi này có hiệu lực ngay lập tức", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
@is_admin()
async def xoauser(ctx, user_id: str):
    """Xóa user khỏi danh sách admin"""
    try:
        user_id_int = int(user_id)
    except ValueError:
        await ctx.send("❌ ID user không hợp lệ!")
        return
    
    if user_id_int not in ADMIN_IDS:
        await ctx.send("❌ User không có trong danh sách admin!")
        return
    
    if len(ADMIN_IDS) <= 1:
        await ctx.send("❌ Không thể xóa admin cuối cùng!")
        return
    
    if user_id_int == ctx.author.id:
        await ctx.send("❌ Bạn không thể tự xóa chính mình!")
        return
    
    # Xóa user khỏi ADMIN_IDS
    ADMIN_IDS.remove(user_id_int)
    
    embed = discord.Embed(title="✅ Xóa User Admin Thành Công", color=0x00ff00)
    embed.add_field(name="User ID", value=f"`{user_id_int}`", inline=False)
    embed.add_field(name="Tổng số admin", value=f"**{len(ADMIN_IDS)}** users", inline=True)
    
    await ctx.send(embed=embed)

@bot.command()
@is_admin()
async def danhsachuser(ctx):
    """Hiển thị danh sách tất cả admin"""
    embed = discord.Embed(title="👥 Danh Sách Admin", color=0x7289da)
    
    user_list = []
    for user_id in ADMIN_IDS:
        try:
            user = await bot.fetch_user(user_id)
            user_info = f"`{user_id}` - {user.name}#{user.discriminator}"
            if user_id == ctx.author.id:
                user_info += " 👈 (Bạn)"
            user_list.append(user_info)
        except:
            user_list.append(f"`{user_id}` - Không tìm thấy user")
    
    embed.add_field(name="Tổng số admin", value=f"**{len(ADMIN_IDS)}** users", inline=False)
    embed.add_field(name="Danh sách", value="\n".join(user_list), inline=False)
    
    await ctx.send(embed=embed)

# ===============================
# 📅 GIA HẠN KEY
# ===============================

@bot.command()
@is_admin()
async def giahankey(ctx, key: str, them_ngay: int):
    """Gia hạn thêm ngày cho key"""
    if them_ngay <= 0:
        await ctx.send("❌ Số ngày gia hạn phải lớn hơn 0!")
        return
    
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    key_found = False
    for k in current_data:
        if k['key'] == key:
            if k.get('unlimited'):
                await ctx.send("❌ Key unlimited không thể gia hạn!")
                return
            
            if not k.get('expires'):
                await ctx.send("❌ Key này không có thời hạn!")
                return
            
            # Tính ngày hết hạn mới
            old_expiry = datetime.datetime.fromisoformat(k['expires'].replace('Z', ''))
            new_expiry = old_expiry + datetime.timedelta(days=them_ngay)
            k['expires'] = new_expiry.isoformat()
            
            days_left = (new_expiry - datetime.datetime.utcnow()).days
            key_found = True
            break
    
    if not key_found:
        await ctx.send("❌ Key không tồn tại!")
        return
    
    if await manager.update_json(current_data):
        embed = discord.Embed(title="✅ Gia Hạn Key Thành Công", color=0x00ff00)
        embed.add_field(name="Key", value=f"`{key}`", inline=False)
        embed.add_field(name="Thêm ngày", value=f"**+{them_ngay}** ngày", inline=True)
        embed.add_field(name="Tổng ngày còn lại", value=f"**{days_left}** ngày", inline=True)
        embed.add_field(name="Hết hạn vào", value=new_expiry.strftime("%d/%m/%Y %H:%M UTC"), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Lỗi khi gia hạn key!")

# ===============================
# 🗑️ XÓA KEY HẾT HẠN
# ===============================

@bot.command()
@is_admin()
async def xoakeyhethan(ctx):
    """Xóa tất cả key đã hết hạn"""
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    if not current_data:
        await ctx.send("📭 Không có key nào trong hệ thống!")
        return
    
    expired_keys = manager.get_expired_keys(current_data)
    
    if not expired_keys:
        await ctx.send("✅ Không có key nào hết hạn!")
        return
    
    new_data = []
    expired_count = 0
    
    for key in current_data:
        if key.get('expires'):
            expiry_date = datetime.datetime.fromisoformat(key['expires'].replace('Z', ''))
            if expiry_date >= datetime.datetime.utcnow():
                new_data.append(key)
            else:
                expired_count += 1
        else:
            new_data.append(key)
    
    embed = discord.Embed(title="⚠️ XÓA KEY HẾT HẠN", color=0xffa500)
    embed.add_field(name="Số key sẽ xóa", value=f"**{expired_count}** keys", inline=False)
    embed.add_field(name="Số key sẽ giữ lại", value=f"**{len(new_data)}** keys", inline=False)
    
    expired_list = "\n".join([f"`{key['key']}` - {key['type']}" for key in expired_keys[:5]])
    if len(expired_keys) > 5:
        expired_list += f"\n... và {len(expired_keys) - 5} keys khác"
    
    embed.add_field(name="Key hết hạn", value=expired_list, inline=False)
    embed.add_field(name="Xác nhận", value="React với ✅ để xóa, ❌ để hủy", inline=False)
    
    confirm_msg = await ctx.send(embed=embed)
    await confirm_msg.add_reaction("✅")
    await confirm_msg.add_reaction("❌")
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
    
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        
        if str(reaction.emoji) == "✅":
            if await manager.update_json(new_data):
                embed_success = discord.Embed(title="✅ Xóa Key Hết Hạn Thành Công", color=0x00ff00)
                embed_success.add_field(name="Đã xóa", value=f"**{expired_count}** keys hết hạn", inline=True)
                embed_success.add_field(name="Còn lại", value=f"**{len(new_data)}** keys", inline=True)
                await confirm_msg.edit(embed=embed_success)
                await confirm_msg.clear_reactions()
            else:
                await ctx.send("❌ Lỗi khi xóa key hết hạn!")
        else:
            embed_cancel = discord.Embed(title="❌ Đã Hủy", color=0xff0000)
            embed_cancel.add_field(name="Thao tác", value="Đã hủy xóa key hết hạn", inline=False)
            await confirm_msg.edit(embed=embed_cancel)
            await confirm_msg.clear_reactions()
            
    except asyncio.TimeoutError:
        embed_timeout = discord.Embed(title="⏰ Hết Giờ", color=0xffa500)
        embed_timeout.add_field(name="Thao tác", value="Đã hết thời gian xác nhận", inline=False)
        await confirm_msg.edit(embed=embed_timeout)
        await confirm_msg.clear_reactions()

# ===============================
# 🔑 KÍCH HOẠT KEY
# ===============================

@bot.command()
@is_admin()
async def kichhoat(ctx, key: str, hwid: str):
    """Kích hoạt key single với HWID"""
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    key_found = False
    for k in current_data:
        if k['key'] == key:
            if k['type'] != 'single':
                await ctx.send("❌ Key này không phải loại single!")
                return
            
            k['hwid'] = hwid
            key_found = True
            break
    
    if not key_found:
        await ctx.send("❌ Key không tồn tại!")
        return
    
    if await manager.update_json(current_data):
        embed = discord.Embed(title="✅ Kích Hoạt Thành Công", color=0x00ff00)
        embed.add_field(name="Key", value=f"`{key}`", inline=False)
        embed.add_field(name="HWID", value=f"`{hwid}`", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Lỗi khi kích hoạt key!")

# ===============================
# 📊 DANH SÁCH & THỐNG KÊ
# ===============================

@bot.command()
@is_admin()
async def danhsachkey(ctx, page: int = 1):
    """Hiển thị danh sách FULL tất cả keys (phân trang)"""
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    if not current_data:
        await ctx.send("📭 Không có key nào trong hệ thống!")
        return
    
    items_per_page = 10
    total_pages = (len(current_data) + items_per_page - 1) // items_per_page
    
    if page < 1 or page > total_pages:
        await ctx.send(f"❌ Trang không hợp lệ! Chọn từ 1 đến {total_pages}")
        return
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_data = current_data[start_idx:end_idx]
    
    embed = discord.Embed(
        title=f"📋 DANH SÁCH TẤT CẢ KEYS (Trang {page}/{total_pages})", 
        color=0x0099ff
    )
    
    for i, key in enumerate(page_data, start=start_idx + 1):
        status = "✅ Đã kích hoạt" if key['hwid'] else "⏳ Chưa kích hoạt"
        
        if key.get('unlimited'):
            expiry_info = "♾️ Vĩnh viễn"
        elif key.get('expires'):
            expiry_date = datetime.datetime.fromisoformat(key['expires'].replace('Z', ''))
            days_left = (expiry_date - datetime.datetime.utcnow()).days
            if days_left > 0:
                expiry_info = f"🟢 {days_left} ngày"
            else:
                expiry_info = "🔴 Hết hạn"
        else:
            expiry_info = "❓ Không xác định"
        
        embed.add_field(
            name=f"#{i} - `{key['key']}`",
            value=f"**Loại:** {key['type']}\n**Trạng thái:** {status}\n**Hạn sử dụng:** {expiry_info}",
            inline=False
        )
    
    single_keys = [k for k in current_data if k['type'] == 'single']
    multi_keys = [k for k in current_data if k['type'] == 'multi']
    unlimited_keys = [k for k in current_data if k.get('unlimited')]
    expired_keys = manager.get_expired_keys(current_data)
    
    embed.set_footer(text=f"🔐 Single: {len(single_keys)} | 👥 Multi: {len(multi_keys)} | ♾️ Unlimited: {len(unlimited_keys)} | 🔴 Hết hạn: {len(expired_keys)} | 📊 Tổng: {len(current_data)}")
    
    message = await ctx.send(embed=embed)
    
    if total_pages > 1:
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["⬅️", "➡️"] and 
                   reaction.message.id == message.id)
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "➡️" and page < total_pages:
                await message.delete()
                await danhsachkey(ctx, page + 1)
            elif str(reaction.emoji) == "⬅️" and page > 1:
                await message.delete()
                await danhsachkey(ctx, page - 1)
            else:
                await message.clear_reactions()
                
        except asyncio.TimeoutError:
            await message.clear_reactions()

@bot.command()
@is_admin()
async def thongke(ctx):
    """Chỉ hiển thị số lượng từng loại key (đơn giản)"""
    manager = KeyManager(GITHUB_TOKEN, GITHUB_REPO)
    current_data = await manager.get_current_json()
    
    if not current_data:
        await ctx.send("📭 Không có key nào trong hệ thống!")
        return
    
    single_keys = [k for k in current_data if k['type'] == 'single']
    multi_keys = [k for k in current_data if k['type'] == 'multi']
    unlimited_keys = [k for k in current_data if k.get('unlimited')]
    expired_keys = manager.get_expired_keys(current_data)
    
    embed = discord.Embed(title="📈 Thống Kê Loại Key", color=0x00ff00)
    embed.add_field(name="🔐 Single Keys", value=f"**{len(single_keys)}** keys", inline=True)
    embed.add_field(name="👥 Multi Keys", value=f"**{len(multi_keys)}** keys", inline=True)
    embed.add_field(name="♾️ Unlimited Keys", value=f"**{len(unlimited_keys)}** keys", inline=True)
    embed.add_field(name="🔴 Key Hết Hạn", value=f"**{len(expired_keys)}** keys", inline=True)
    embed.add_field(name="📊 Tổng Cộng", value=f"**{len(current_data)}** keys", inline=True)
    
    await ctx.send(embed=embed)

# ===============================
# 📋 MENU & HELP
# ===============================

@bot.command()
@is_admin()
async def menu(ctx):
    """Hiển thị tất cả lệnh có sẵn"""
    try:
        # Embed 1: Lệnh tạo và quản lý key
        embed1 = discord.Embed(
            title="🛠️ MENU LỆNH QUẢN LÝ KEY - PHẦN 1", 
            description="**LỆNH TẠO VÀ QUẢN LÝ KEY**",
            color=0x7289da
        )
        
        embed1.add_field(
            name="🎯 **LỆNH TẠO KEY:**",
            value="`!taokey <type> <amount> [days]`\nTạo key tùy chọn (single/multi/unlimited)",
            inline=False
        )
        
        embed1.add_field(
            name="🔧 **LỆNH QUẢN LÝ KEY:**",
            value=(
                "`!xoakey <key1> <key2> ...` - Xóa một hoặc nhiều key\n"
                "`!xoakeyhethan` - Xóa tất cả key đã hết hạn\n"
                "`!kichhoat <key> <hwid>` - Kích hoạt key single với HWID\n"
                "`!resetHWID <key>` - Reset HWID cho key (user đổi máy)\n"
                "`!giahankey <key> <số_ngày>` - Gia hạn thêm ngày cho key"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed1)
        
        # Embed 2: Lệnh admin và thống kê
        embed2 = discord.Embed(
            title="🛠️ MENU LỆNH QUẢN LÝ KEY - PHẦN 2", 
            description="**LỆNH QUẢN LÝ ADMIN & THỐNG KÊ**",
            color=0x7289da
        )
        
        embed2.add_field(
            name="👥 **LỆNH QUẢN LÝ ADMIN:**",
            value=(
                "`!themuser <user_id>` - Thêm user vào danh sách admin\n"
                "`!xoauser <user_id>` - Xóa user khỏi danh sách admin\n"
                "`!danhsachuser` - Xem danh sách admin"
            ),
            inline=False
        )
        
        embed2.add_field(
            name="📊 **LỆNH XEM THỐNG KÊ:**",
            value=(
                "`!danhsachkey [page]` - Xem danh sách FULL keys (phân trang)\n"
                "`!thongke` - Xem nhanh số lượng từng loại key\n"
                "`!menu` - Hiển thị menu này\n"
                "`!help` - Hiển thị hướng dẫn sử dụng"
            ),
            inline=False
        )
        
        embed2.add_field(
            name="📝 **CÁCH SỬ DỤNG:**",
            value=(
                "**<tham_số>** - Tham số bắt buộc\n"
                "**[tham_số]** - Tham số tùy chọn\n"
                "**type** - single, multi, unlimited\n"
                "**amount** - Số lượng key cần tạo\n"
                "**days** - Số ngày sử dụng (mặc định: 30)"
            ),
            inline=False
        )
        
        embed2.set_footer(text="🤖 Bot Quản Lý Key - GitHub Integration | 🚄 Railway 24/7")
        await ctx.send(embed=embed2)
        
    except Exception as e:
        await ctx.send(f"❌ Đã xảy ra lỗi khi hiển thị menu: {str(e)}")

@bot.command()
async def help(ctx):
    """Hiển thị hướng dẫn sử dụng"""
    try:
        embed = discord.Embed(
            title="📖 HƯỚNG DẪN SỬ DỤNG BOT", 
            description="Hướng dẫn chi tiết cách sử dụng các lệnh quản lý key",
            color=0x7289da
        )
        
        embed.add_field(
            name="🎯 **TẠO KEY:**",
            value=(
                "`!taokey single 1 30` - Tạo 1 key single 30 ngày\n"
                "`!taokey multi 5 60` - Tạo 5 key multi 60 ngày\n"
                "`!taokey unlimited 3` - Tạo 3 key unlimited"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 **QUẢN LÝ KEY:**",
            value=(
                "`!xoakey ABC123` - Xóa 1 key\n"
                "`!xoakey ABC123 DEF456` - Xóa nhiều key cùng lúc\n"
                "`!resetHWID ABC123` - Reset HWID khi user đổi máy\n"
                "`!giahankey ABC123 30` - Gia hạn thêm 30 ngày\n"
                "`!kichhoat ABC123 HWID123` - Kích hoạt key với HWID\n"
                "`!xoakeyhethan` - Xóa key hết hạn"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👥 **QUẢN LÝ ADMIN:**",
            value=(
                "`!themuser 123456789` - Thêm admin mới\n"
                "`!xoauser 123456789` - Xóa admin\n"
                "`!danhsachuser` - Xem danh sách admin"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 **XEM THỐNG KÊ:**",
            value=(
                "`!danhsachkey` - Xem danh sách FULL keys\n"
                "`!thongke` - Xem thống kê nhanh\n"
                "`!menu` - Xem menu đầy đủ"
            ),
            inline=False
        )
        
        embed.set_footer(text="🤖 Sử dụng !menu để xem tất cả lệnh | 🚄 Railway 24/7")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Đã xảy ra lỗi khi hiển thị help: {str(e)}")

# ===============================
# ⚠️ XỬ LÝ LỖI
# ===============================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Thiếu tham số! Sử dụng `!menu` để xem hướng dẫn.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Tham số không hợp lệ! Sử dụng `!menu` để xem hướng dẫn.")
    else:
        await ctx.send("❌ Đã xảy ra lỗi! Vui lòng thử lại.")
        print(f"Lỗi không xác định: {error}")

# ===============================
# 🚀 CHẠY BOT
# ===============================
if __name__ == "__main__":
    print("🚀 Đang khởi động Bot Discord...")
    print("🚄 Kích hoạt chế độ Railway 24/7...")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Lỗi khi chạy bot: {e}")
