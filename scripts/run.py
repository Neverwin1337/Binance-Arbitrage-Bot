import asyncio
from arbitrage.arb import ArbBot


async def main() -> None:
    bot = ArbBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())