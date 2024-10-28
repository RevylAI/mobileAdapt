# Cognisim

[Company Website](https://revyl.ai) | [Twitter](https://x.com/tryrevyl) |

![Revyl AI Logo](.github/assets/dark_logo.png)





### Interaction utilies for crossplatform interaction agents

**LLM Control Library for iOS and Android**

Have you ever wanted to test your mobile app or control iOS and Android devices with an LLM? You've probably encountered context problems due to the accessibility view being too long or just sending a screenshot to the LLM, which provides limited accuracy.


<video src=".github/assets/mobile_adapt_example.mp4" width="500" height="600" controls></video>
(example of using cognisim to control an android device on the arcteryx app (bout to be dripped out))


**Our Solution**

We combine the accessibility tree with a set of mark prompting to provide a readable state for the LLM.

**Real-World Application**

At Revyl, we use this approach to test mobile apps with LLMs. Our platform integrates resilient end-to-end tests using agentic LLMs with open telemetry tracing, offering proactive observability into your mobile app.

If you are interested in putting your testing on autopilot, and catching bugs before your users do, 



[book a demo with us](https://cal.com/landseer-enga/book-a-demo)


#### [Revyl AI](https://revyl.ai)

### Prerequisites

- Android Virtual Device (for Android adaptation)
- iOS Simulator and Xcode (for iOS adaptation - coming soon)
- macOS or Linux (recommended)


## Quick Start


Create a Simulator with ios/android and make sure you have appium installed


For macOS, install Appium using Homebrew:
```bash
brew install appium
```

For all other operating systems, install Appium using npm:
```bash
npm i -g appium
```


To install the mobileadapt package:


```bash
poetry add cognisim
```      
or if you have pip installed:

```bash
pip install cognisim
```

For detailed instructions on getting started with Mobileadapt, please refer to our [Quickstart Guide](https://mobileadapt.revyl.ai/quickstart).



# Usage
### Android Basic Example

```python
import asyncio
from cognisim import mobileadapt

async def main():
    # Initialize and start Android device
    android_device = mobileadapt(platform="android")
    await android_device.start_device()

    # Get initial state and perform tap
    _, _, _ = await android_device.get_state()
    await android_device.tap(100, 100)

    # Get state after tap
    new_encoded_ui, _, _ = await android_device.get_state()
    print("State after tap:", new_encoded_ui)

if __name__ == "__main__":
    asyncio.run(main())
```

### IOS Basic Example

```python
import asyncio
from cognisim import mobileadapt

async def main():
    # Initialize and start iOS device
    ios_device = mobileadapt(platform="ios")
    await ios_device.start_device()

    # Get device state
    encoded_ui, _, _ = await ios_device.get_state()
    print("Current state:", encoded_ui)

if __name__ == "__main__":
    asyncio.run(main())
```

### Go to [Documentation](https://mobileadapt.revyl.ai) or the cookbook folder for more examples and usage.




## Documentation

For full documentation, visit [mobileadapt.revyl.ai](https://mobileadapt.revyl.ai).


## Key Features

- **Android Support**: Works seamlessly with Android devices and emulators.

- **IOS Support**: Works seamlessly with Android devices and emulators.
- **Appium Integration**: Leverages the power of Appium for reliable mobile automation.
- **LLM Agent Compatibility**: Designed to work seamlessly with language model agents.
- **iOS Support**: Coming soon!




### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/RevylAI/Mobileadapt/ && cd mobileadapt/deploy
   ```

2. Start the server:
   ```bash
   ./scripts/setup.sh
   ```

## Roadmap
- [x] iOS Support
- [ ] Abstract to different drivers other than appium
- [ ] Recording interactions
- [ ] Screen sharing via websocket to host recording




## Contributing

We welcome contributions to the Mobileadapt project! If you'd like to contribute, please check our [Contribution Guidelines](https://github.com/RevylAI/Mobileadapt/blob/main/CONTRIBUTING.md).

## License

Mobileadapt is released under the MIT License. See the [LICENSE](https://github.com/RevylAI/Mobileadapt/blob/main/LICENSE) file for more details.



# Credits

@inproceedings{shvoEtAl2021appbuddy,
  title={AppBuddy: Learning to Accomplish Tasks in Mobile Apps via Reinforcement Learning},
  author={Maayan Shvo and
               Zhiming Hu and
               Rodrigo Toro Icarte and
               Iqbal Mohomed and
               Allan D. Jepson and
               Sheila A. McIlraith},
  booktitle={Canadian Conference on Artificial Intelligence},
  year={2021}
}

@misc{google-research,
  title={Google Research},
  author={Google},
  year={2021},
  howpublished={\url{https://github.com/Berrylcm/google-research}}
}




## How does it work?

We use Appium under the hood to control the device and collect the UI. We then use a custom UI parser to convert the UI to a string that can be used by the LLM.


The UI is parsed with a ui parser and then set of mark is generated for the image and we send that to the LLM..

The UI is parsed with a ui parser and then a set of marks is generated for the image, and we send that to the LLM. For example, the parsed UI might look like this:

```   html
<html>
  <button id=0">None</button>
  <button id=1 class="home_button">Open the home page</button>
  <button id=2 class="optional_toolbar_button">New tab</button>
  <button id=3 class="tab_switcher_button">Switch or close tabs</button>
  <button id=4 class="menu_button">Customize and control Google Chrome</button>
  <input id=5 class="url_bar">revyl.ai</input>
  <img id=6 class="location_bar_status_icon" alt="Connection is secure" />
  <p id=7">None</p>
  <img id=8 class="toolbar_hairline" alt="None" />
  <button id=9">Dismiss banner</button>
  <p id=10">Revyl is in private beta →</p>
  <p id=11">None</p>
  <button id=12">Menu</button>
  <p id=13">Revyl</p>
  <button id=14">None</button>
  <button id=15">None</button>
  <p id=16">None</p>
  <p id=17">AI Native Proactive Observability</p>
  <p id=18">Catch bugs</p>
  <p id=19">they happen using agentic E2E testing and OpenTelemetry's Tracing. Book a demo</p>
  <p id=20">before</p>
  <p id=21">now</p>
  <p id=22">!</p>
  <button id=23">Join the waitlist →</button>
  <p id=24">Book a demo</p>
  <button id=25">None</button>
  <p id=26">TRUSTED AND BUILT BY ENGINEERS AT</p>
  <button id=27">Uber</button>
  <button id=28">Salesforce</button>
  <p id=29">VendorPM</p>
</html>
```

This structured representation of the UI elements is then used by the LLM to understand and interact with the mobile interface.

Each of the ids are mapped to an element in the UI.

We also create a set of mark prompting of the given state



Here's an example of a set of mark image generated for the UI state:

<img src=".github/assets/set_of_mark.png" width="500" height="600">

This image shows the UI elements with their corresponding IDs overlaid on the screenshot. This visual representation helps the LLM understand the layout and structure of the interface, making it easier to interact with specific elements.

## Citations

```
bibtex
@misc{revylai2024mobileadapt,
  title        = {Cognisim},
  author       = {Anam Hira, Landseer Enga, Aarib Sarker, Wasif Sarker, Hanzel Hira, Sushan Leel},
  year         = {2024},
  howpublished = {GitHub},
  url          = {https://github.com/RevylAI/Mobileadapt}
}
```