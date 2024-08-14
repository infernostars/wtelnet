from libs.enhrewr import TelnetController, KeyedOption
import libs.user, colored, config
from libs.utils import UserNotFoundException, UsernameInUseException, whirlnet_textstyle
from handling.shell_mode import ShellManager
async def entry(ctx: TelnetController):
    ctx.write_title(f"whirlnet")
    ctx.write(f"{colored.Fore.light_yellow}\r\n{config.MOTD}{colored.Style.reset}")
    login_type = await ctx.prompt_keylist([KeyedOption("l", "login"),
                                           KeyedOption("s", "signup")])
    if login_type is None:
        raise Exception()
    await login(login_type, ctx)
    print(ctx.user)
    ctx.cls()
    sh_manager = ShellManager()
    shell = await sh_manager.create_shell(ctx)
    await shell.run()
    ctx.close()

async def login(login_type: KeyedOption, ctx: TelnetController):
    ctx.cls()
    if login_type.key == "l": await login_user(ctx)
    if login_type.key == "s": await signup_user(ctx)

async def login_user(ctx: TelnetController):
    ctx.write_title(f"whirlnet login")
    username = await ctx.prompt_text(whirlnet_textstyle("username") + " //", max_len=64)
    password = await ctx.prompt_text(whirlnet_textstyle("password (not echoed, max 64)") + " //", echo=False, max_len=64)
    try:
        user = libs.user.login(username, password)
        ctx.user = user
    except UserNotFoundException:
        ctx.cls()
        ctx.write("That user wasn't found, or the password was invalid.")
        ctx.newline()
        await login_user(ctx)
        return

async def signup_user(ctx: TelnetController):
    ctx.write_title(f"whirlnet signup")
    username = await ctx.prompt_text(whirlnet_textstyle("username") + " //", max_len=64)
    password = await ctx.prompt_text(whirlnet_textstyle("password (not echoed, max 64)") + " //", echo=False, max_len=64)
    password2 = await ctx.prompt_text(whirlnet_textstyle("password again to confirm") + " //", echo=False, max_len=64)
    if len(password) == 0:
        ctx.cls()
        ctx.write("Your password can't be blank!")
        ctx.newline()
        await signup_user(ctx)
        return
    if len(username) < 3:
        ctx.cls()
        ctx.write("Your username must be at least 3 characters!")
        ctx.newline()
        await signup_user(ctx)
        return
    if password == password2:
        try:
            libs.user.register_user(username, password)
        except UsernameInUseException as e:
            ctx.cls()
            ctx.write("The username is in use! try again.")
            ctx.newline()
            await signup_user(ctx)
            return
        ctx.cls()
        ctx.write("User created! Please log in.")
        ctx.newline()
        await login_user(ctx)
