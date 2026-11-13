# Hessen Holiday Witness

An experimental GenLayer Intelligent Contract that checks whether a date is listed as a public holiday in Hesse, Germany.

## How it works

The caller provides a date in `YYYY-MM-DD` format. The contract fetches the matching year's JSON holiday list from Nager.Date, includes national holidays and holidays explicitly marked for Hesse (`DE-HE`), and requires validator agreement on the matching holiday details. It stores the result, source URL, and SHA-256 response digest.

Nager.Date is community-maintained, not a government authority. This contract provides informational data, not legal advice.

## Live Studio result

- Contract: `0x41441E378Ff08C522850bD5b63B37466918d16c2`
- Deployment: [0xce356c3dc0cacd5dbfbb95012586c6fe4238a6bbe3550ebb071c2efecf30f555](https://explorer-studio.genlayer.com/tx/0xce356c3dc0cacd5dbfbb95012586c6fe4238a6bbe3550ebb071c2efecf30f555)
- Check: [0xc60bb1ed77b7963c28194dd925442bede34d93c9af9b3f115432c7ee46994966](https://explorer-studio.genlayer.com/tx/0xc60bb1ed77b7963c28194dd925442bede34d93c9af9b3f115432c7ee46994966)
- Stored record: ID `0`, status `PUBLIC_HOLIDAY`
- Date: `2026-06-04`, Corpus Christi (`Fronleichnam`)
- Response SHA-256: `8738a17bd15d67d9afefde657b10059919aced6fb1133d39f5fed9991fe6a3bb`

## Development

Install dependencies with `python -m pip install -r requirements-dev.txt`. Run `python -m py_compile contracts/holiday_witness.py` and `python -m pytest -q`.

The eight local tests cover date validation and holiday-data parsing. They do not replace live GenLayer consensus testing.

## License

MIT. See `LICENSE`.
