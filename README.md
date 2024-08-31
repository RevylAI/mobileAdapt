# Mobileadapt: Crossplatform Mobile LLM Agents

Mobileadapt is a powerful tool built on top of Appium that enables the creation of mobile LLM (Language Model) agents for android, and ios . This project aims to bridge the gap between large language models and mobile device interaction, allowing for more sophisticated automation and testing capabilities.

## Key Features

- **Android Support**: Works seamlessly with Android devices and emulators.
- **Appium Integration**: Leverages the power of Appium for reliable mobile automation.
- **LLM Agent Compatibility**: Designed to work seamlessly with language model agents.
- **iOS Support**: Coming soon!

## Quick Start

```bash

poetry add mobileadapt
```      
or if you have pip installed:

```bash
pip install mobileadapt
```

For detailed instructions on getting started with Mobileadapt, please refer to our [Quickstart Guide](https://mobileadapt.revyl.ai/quickstart).

### Prerequisites

- Android Virtual Device (for Android adaptation)
- iOS Simulator and Xcode (for iOS adaptation - coming soon)
- macOS or Linux (recommended)

###Local Development

1. Clone the repository:
   ```bash
   git clone --branch main https://github.com/RevylAI/Mobileadapt/ && cd mobileadapt/deploy
   ```

2. Start the server:
   ```bash
   ./scripts/setup.sh
   ```

## Documentation

For full documentation, visit [mobileadapt.revyl.ai](https://mobileadapt.revyl.ai).

## Roadmap
- [ ] iOS Support
- [ ] Recording interactions


## Contributing

We welcome contributions to the Mobileadapt project! If you'd like to contribute, please check our [Contribution Guidelines](https://github.com/RevylAI/Mobileadapt/blob/main/CONTRIBUTING.md).

## License

Mobileadapt is released under the MIT License. See the [LICENSE](https://github.com/RevylAI/Mobileadapt/blob/main/LICENSE) file for more details.

## Citations

```
bibtex
@misc{revylai2024mobileadapt,
  title        = {Mobileadapt},
  author       = {Anam Hira, Landseer Enga, Aarib Sarker, Wasif Sarker, Hanzel Hira, Sushan Leel},
  year         = {2024},
  howpublished = {GitHub},
  url          = {https://github.com/RevylAI/Mobileadapt}
}
```