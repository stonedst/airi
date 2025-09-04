<script setup lang="ts">
import type { SpeechProvider } from '@xsai-ext/shared-providers'

import {
  SpeechPlayground,
  SpeechProviderSettings,
} from '@proj-airi/stage-ui/components'
import { useSpeechStore } from '@proj-airi/stage-ui/stores/modules/speech'
import { useProvidersStore } from '@proj-airi/stage-ui/stores/providers'
import { storeToRefs } from 'pinia'
import { computed } from 'vue'

const providerId = 'edge-tts'
const defaultModel = 'edge-tts'

const speechStore = useSpeechStore()
const providersStore = useProvidersStore()
const { providers } = storeToRefs(providersStore)

// Check if service is accessible
const serviceAccessible = computed(() => !!providers.value[providerId]?.baseUrl)

// Get available voices
const availableVoices = computed(() => {
  return speechStore.availableVoices[providerId] || []
})

// Generate speech
async function handleGenerateSpeech(input: string, voiceId: string, _useSSML: boolean) {
  const provider = await providersStore.getProviderInstance(providerId) as SpeechProvider
  if (!provider) {
    throw new Error('Failed to initialize Edge TTS provider')
  }

  // Get provider configuration
  const providerConfig = providersStore.getProviderConfig(providerId)

  // Call the Python service
  const baseUrl = providerConfig.baseUrl as string
  const response = await fetch(`${baseUrl}tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: input,
      voice: voiceId,
    }),
  })

  if (!response.ok) {
    throw new Error(`Edge TTS service error: ${response.statusText}`)
  }

  const arrayBuffer = await response.arrayBuffer()
  return arrayBuffer
}
</script>

<template>
  <SpeechProviderSettings
    :provider-id="providerId"
    :default-model="defaultModel"
  >
    <template #playground>
      <SpeechPlayground
        :available-voices="availableVoices"
        :generate-speech="handleGenerateSpeech"
        :api-key-configured="serviceAccessible"
        default-text="你好！这是 Edge TTS 语音合成测试。Hello! This is a test of the Edge TTS voice synthesis."
      />
    </template>
  </SpeechProviderSettings>
</template>

<route lang="yaml">
meta:
  layout: settings
  stageTransition:
    name: slide
</route>
